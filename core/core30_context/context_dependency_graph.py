from __future__ import annotations

from ..core99_misc.fakejq.utils import check_dict_against_attributes_string

from typing import Callable, Any, Tuple, Type, Union
from contextvars import ContextVar, Context
from functools import wraps
import networkx as nx
import copy


class ThreadSafeDependencyManager:
    _global_context_dependencies_graph = nx.DiGraph()
    _global_context_nodes = {}
    _global_context_producers = {}
    _global_context_consumers = {}

    _incontext_dependencies_graph = ContextVar('dependencies_graph')
    _incontext_nodes = ContextVar('context_nodes')
    _incontext_producers = ContextVar('context_producers')
    _incontext_consumers = ContextVar('context_consumers')
    _incontext_dependencies_graph.set(_global_context_dependencies_graph)
    _incontext_nodes.set(_global_context_nodes)
    _incontext_producers.set(_global_context_producers)
    _incontext_consumers.set(_global_context_consumers)

    @classmethod
    def _set_default(cls):
        cls._incontext_dependencies_graph.set(cls._global_context_dependencies_graph)
        cls._incontext_nodes.set(cls._global_context_nodes)
        cls._incontext_producers.set(cls._global_context_producers)
        cls._incontext_consumers.set(cls._global_context_consumers)


    # _thread_local = threading.local()  # legacy with thread_local

    @classmethod
    def copy_dependencies_context(cls, ctxt: Context | None = None):
        try:
            dependencies_graph = cls._incontext_dependencies_graph.get()
            nodes = cls._incontext_nodes.get()
            producers = cls._incontext_producers.get()
            consumers = cls._incontext_consumers.get()
        except:
            cls._set_default()
        ctxt = Context() if not ctxt else ctxt

        def _copy_context():
            cls._incontext_dependencies_graph.set(dependencies_graph.copy())
            cls._incontext_nodes.set(copy.deepcopy(nodes))
            cls._incontext_producers.set(copy.deepcopy(producers))
            cls._incontext_consumers.set(copy.deepcopy(consumers))

        ctxt.run(_copy_context)
        return ctxt

    @classmethod
    def get_attr_or_copy_from_global(cls, attr_name):
        attribute = getattr(cls, '_in' + attr_name)
        try:
            return attribute.get()
        except:  # this will happen in new threads
            attribute.set(
                getattr(cls, '_global_' + attr_name).copy() if attr_name == '_incontext_dependencies_graph' else
                copy.deepcopy(getattr(cls, '_global_' + attr_name))
            )
        return getattr(cls, '_in' + attr_name).get()
        # legacy with thread_local
        # if threading.current_thread() is threading.main_thread():
        #     return getattr(cls, '_' + attr_name).set()
        # else:
        #     if not hasattr(cls._thread_local, attr_name):
        #         # the first time in a thread the variable is asked, copy it from its global state
        #         setattr(cls._thread_local, attr_name,
        #                 getattr(cls, '_' + attr_name).copy() if attr_name == '_context_dependencies_graph' else
        #                 copy.deepcopy(getattr(cls, '_' + attr_name)))
        #     return getattr(cls._thread_local, attr_name)

    def __init__(self):
        self.context_dependencies_graph = ThreadSafeDependencyManager.get_attr_or_copy_from_global(
            'context_dependencies_graph')
        self.context_nodes = ThreadSafeDependencyManager.get_attr_or_copy_from_global('context_nodes')
        self.context_producers = ThreadSafeDependencyManager.get_attr_or_copy_from_global('context_producers')
        self.context_consumers = ThreadSafeDependencyManager.get_attr_or_copy_from_global('context_consumers')

    def add_node_if_not_existing(self, f: Callable[[...], Any]):
        key = f"{f.__module__}.{f.__name__}"
        # assert key not in context_nodes, f"Function node {key} already declared"
        if key not in self.context_nodes:
            self.context_nodes[key] = {'index': len(self.context_nodes)}  # no race condition as thread local
            self.context_dependencies_graph.add_node(self.context_nodes[key]['index'], name=key)
        return key, self.context_nodes[key]['index']

    # the function below aims at handling the dependencies graph (resolving when needed)
    def context_dependencies(self, *deps: Union[Tuple[str, Type], Tuple[str, Type, bool]]):
        def sub(f: Callable[[...], Any]):
            key, node_target_index = self.add_node_if_not_existing(f)

            assert 'dependencies' not in self.context_nodes[key], f"Dependencies for {key} already registered"
            self.context_nodes[key].update({
                'dependencies': {dep[0]: dep[1:]
                                 for dep in deps},  # dependencies are for checking type coherence and needing producer
                'dependencies_ok': False,  # only these 2 variables are used below
                'dependencies_doing': False,  # this one intends to prevent cycles in dependencies graph
            })
            for dep in deps:
                dep_name = dep[0]
                assert dep_name[0] == '.', f"Value to produce {dep_name} not starting with dot (pyjq like)"
                self.context_consumers.setdefault(dep_name, []).append(node_target_index)
                if dep_name in self.context_producers:
                    self.context_dependencies_graph.add_edge(self.context_producers[dep_name], node_target_index)

            @wraps(f)
            def f_with_deps_resolved(*args, **argv):
                current_ctxt()  # this is a little hack to recreate the right context and dependencies
                if not self.context_nodes[key].get('dependencies_ok'):
                    assert not self.context_nodes[key]['dependencies_doing'], \
                        f"Cycle encountered at {key} for producing {self.context_nodes[key].get('products', '?')}"
                    # indicates we are walking on dependencies recursively
                    self.context_nodes[key]['dependencies_doing'] = True
                    for dep in deps:
                        if len(dep) == 2:
                            attributes_string, expected_type = dep
                            needing_a_fixed_producer = True
                        else:
                            attributes_string, expected_type, needing_a_fixed_producer = dep
                        if needing_a_fixed_producer:
                            assert attributes_string in self.context_producers, \
                                f"No context producer registered to craft {attributes_string}, please register one"

                        if needing_a_fixed_producer or attributes_string in self.context_producers:
                            producer_name = self.context_dependencies_graph.nodes[
                                self.context_producers[attributes_string]
                            ]['name']
                            producer_node = self.context_nodes[producer_name]
                            # check type coherence between producer and consumer
                            assert producer_node['products'][attributes_string] == expected_type, \
                                f"Incompatible types between expected dependency {expected_type} and produced " \
                                f"{producer_node['products'][attributes_string]}"

                            # this must have been registered from a known producer so the optional assert_types and
                            # assert_done are handled by it, but trust the production_ok variable to avoid recomputing
                            if not producer_node['production_ok']:
                                producer_node['produce_function']()
                    self.context_nodes[key]['dependencies_ok'] = True
                    self.context_nodes[key]['dependencies_doing'] = False
                # if the function is not both a consumer and a producer, we add the context (otherwise the producer will do)
                return f(current_ctxt(), *args, **argv) if not self.context_nodes[key].get('products') \
                    else f(*args, **argv)

            return f_with_deps_resolved

        return sub

    def _assert_production(self, key, products, context, assert_done, assert_types):
        if not self.context_nodes[key]['production_ok']:
            if assert_done or assert_types:
                for attributes_string, expected_type in products:
                    success, value = check_dict_against_attributes_string(context, attributes_string)
                    assert success, f"Expected function to produce {attributes_string}, unable to reach {value}"
                    if assert_types:
                        # TODO: proper type validation, as types with [] not handled (raises exception)
                        assert isinstance(value, expected_type), f"Bad produced type {type(value)} instead of " \
                                                                 f"{expected_type}"
            self.context_nodes[key]['production_ok'] = True

    def context_producer(self, *products: Tuple[str, Type], assert_done=True, assert_types=False):
        def sub(f: Callable[[...], Any]):
            key, node_source_index = self.add_node_if_not_existing(f)

            assert not any([product_name in self.context_producers for product_name, _ in products]), \
                f"Context producers {[pname for pname, _ in products if pname in self.context_producers]} already" \
                f" declared"
            assert 'products' not in self.context_nodes[key], f"Producer for {key} already registered"
            self.context_nodes[key].update({
                'products': {pname: ptype for pname, ptype in products},
                'production_ok': False,
            })
            for product_name, _ in products:
                assert product_name[0] == '.', f"Value to produce {product_name} not starting with dot (pyjq like)"
                self.context_producers[product_name] = node_source_index
                for context_consumer_index in self.context_consumers.get(product_name, []):
                    self.context_dependencies_graph.add_edge(node_source_index, context_consumer_index)

            @wraps(f)
            def f_producing_expected(*args, **argv):
                # in fact this should be f(context) as we have no clue of which arguments to provide recursively
                # in the graph to construct the right result
                context = current_ctxt()
                result = f(context, *args, **argv)
                self._assert_production(key, products, context, assert_done, assert_types)
                return result

            # this way the caller can resolve dependency, and it follows the production checks
            self.context_nodes[key].update({'produce_function': f_producing_expected})

            return f_producing_expected

        return sub

    def context_dynamic_producer(self, *products: Tuple[str, Type], assert_done=True, assert_types=False):
        def sub(f: Callable[[...], Any]):
            key, node_source_index = self.add_node_if_not_existing(f)

            assert 'products' not in self.context_nodes[key], f"Dynamic producer for {key} already registered"
            self.context_nodes[key].update({
                'products': {pname: ptype for pname, ptype in products},
                'production_ok': False,
            })
            for product_name, _ in products:
                assert product_name[0] == '.', f"Value to produce {product_name} not starting with dot (pyjq like)"

            @wraps(f)
            def f_producing_expected(*args, **argv):
                # in fact this should be f(context) as we have no clue of which arguments to provide recursively
                # in the graph to construct the right result
                context = current_ctxt()
                result = f(context, *args, **argv)
                self._assert_production(key, products, context, assert_done, assert_types)
                return result

            return f_producing_expected

        return sub

    def try_resolve(self, *dep_names: str):
        producers = {dep_name: self.context_nodes[self.context_dependencies_graph.nodes[
            self.context_producers[dep_name]
        ]['name']] for dep_name in dep_names}
        return {dep_name: producers[dep_name]['produce_function'] for dep_name in dep_names}

    def is_producer(self, function_key: str):
        return self.context_nodes.get(function_key, {}).get('produce_function', None)

    @classmethod
    def _invalidate_graph_index(cls, to_invalidate_set, already_done=None):
        nodes = cls._incontext_nodes.get()
        deps_graph = cls._incontext_dependencies_graph.get()

        next_layer = set()
        already_done = set() if not already_done else already_done
        for producer_idx in to_invalidate_set:
            if producer_idx not in already_done:
                already_done.add(producer_idx)
                nodes[deps_graph.nodes[producer_idx]['name']]['production_ok'] = False
                for src, dst in deps_graph.out_edges(producer_idx):
                    assert src == producer_idx, f"out_edges function failed to return appropriate content"
                    nodes[deps_graph.nodes[dst]['name']]['dependencies_ok'] = False
                    if 'production' in nodes[deps_graph.nodes[dst]['name']]:
                        next_layer.add(dst)
        if next_layer:
            cls._invalidate_graph_index(next_layer, already_done)

    @classmethod
    def invalidate_context_dependencies(cls, *dep_names: str):
        try:
            cls._incontext_producers.get()
        except:
            cls._set_default()
        finally:
            source_producers = cls._incontext_producers.get()

        invalidated_producer_names = set()
        for dep_name in dep_names:
            for attribute_string in source_producers:
                if attribute_string[:len(dep_name) + 1] == dep_name + '.':
                    invalidated_producer_names.add(source_producers[attribute_string])
        cls._invalidate_graph_index(invalidated_producer_names)


def context_dependencies(*deps: Union[Tuple[str, Type], Tuple[str, Type, bool]]):
    return ThreadSafeDependencyManager().context_dependencies(*deps)


def context_producer(*products: Tuple[str, Type], assert_done=True, assert_types=False):
    return ThreadSafeDependencyManager().context_producer(*products, assert_done=assert_done, assert_types=assert_types)


def context_dynamic_producer(*products: Tuple[str, Type], assert_done=True, assert_types=False):
    return ThreadSafeDependencyManager().context_dynamic_producer(*products,
                                                                  assert_done=assert_done, assert_types=assert_types)


def try_resolve(*dep_names: str):
    return ThreadSafeDependencyManager().try_resolve(*dep_names)


def is_context_producer(function_key: str):  # function_key is f.__module__ + . + f.__name__
    return ThreadSafeDependencyManager().is_producer(function_key)


def copy_dependencies_context(ctxt: Context | None = None):  # warning: this Context is from contextvars
    return ThreadSafeDependencyManager.copy_dependencies_context(ctxt)


def invalidate_context_dependencies(*dep_names: str):
    return ThreadSafeDependencyManager.invalidate_context_dependencies(*dep_names)


from .context import current_ctxt
