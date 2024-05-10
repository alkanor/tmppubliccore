#####################
# This must test:
# * multithread use of the dependency graph (shared until thread split, then 2 branches: one main, one other thread)
# * producer missing (dependency not fulfilled) exception
# * cyclic dependencies' exception
# * type incompatibility between producer and consumer
# * dynamic lack of produced attribute after production
# * redeclaration of a producer or a consumer for a function with the same name + module
from core.core30_context.context_dependency_graph import context_producer, context_dependencies, \
    ThreadSafeDependencyManager
from core.core30_context.context import copy_context


# minimal test ok
@context_producer(('.a.a', str))
def produce_a(ctxt):
    print("ok for feeding with .a.a")
    ctxt.setdefault('a', {}).setdefault('a', 'A')

@context_dependencies(('.a.a', str))
def consume_a(ctxt, other_arg):
    return f"{ctxt['a']['a']}-{other_arg}"

def test1():
    print(consume_a("bcd"))


# now declare again any of the producer / consumer, this raises exception, as well as re-declaring producer for string
try:
    @context_producer(('.a.b', int))
    def produce_a(ctxt):
        pass
except AssertionError:
    print("redeclare 1 - good")

try:
    @context_producer(('.a.a', int))
    def produce_anything_on_already_a_a(ctxt):
        pass
except AssertionError:
    print("redeclare 2 - good")

try:
    @context_dependencies(('.a.b', str))
    def consume_a(ctxt, any):
        pass
except AssertionError:
    print("redeclare 3 - good")


# now do not produce the expected modification of context
@context_producer(('.a.b', int))
def produce_anything_on_a_b(ctxt):
    pass

@context_dependencies(('.a.b', int))
def consume_a_b(ctxt, other_arg):
    return f"{ctxt['a']['b']}-{other_arg}"

def test2():
    print(consume_a_b("bcd"))


# now type incompatibility between producer and consumer
@context_producer(('.a.c', int))
def produce_anything_on_a_c(ctxt):
    print("ok for feeding with .a.c")
    ctxt.setdefault('a', {}).setdefault('c', 0x63)

@context_dependencies(('.a.c', str))
def consume_a_c(ctxt, other_arg):
    return f"{ctxt['a']['c']}-{other_arg}"

def test3():
    print(consume_a_c("bcd"))


# more complex setup with several dependencies
@context_producer(('.a.d', str))
@context_dependencies(('.a.e', str), ('.a.c', int))
def produce_d(ctxt):
    print("ok for feeding with .a.d")
    ctxt.setdefault('a', {}).setdefault('d', 'D')

# also test order (should not break anything)
@context_dependencies(('.a.a', str), ('.a.d', int))
@context_producer(('.a.e', str))
def produce_e(ctxt):
    print("ok for feeding with .a.e")
    ctxt.setdefault('a', {}).setdefault('e', 'E')

@context_dependencies(('.a.a', str), ('.a.c', int), ('.a.d', str), ('.a.e', str))
def big_consumer(ctxt, *args):
    return f"{ctxt['a']['a']}-{ctxt['a']['c']}-{ctxt['a']['d']}-{ctxt['a']['e']}-{'_'.join(args)}"

def test4():
    print(big_consumer("also", "we", "are", "here"))

@context_producer(('.a.g', str))
@context_dependencies(('.a.a', str), ('.a.c', int), ('.a.d', str), ('.a.f', str))
def big_consumer_for_cyclic_dep(ctxt, *args):
    ctxt['a']['g'] = f"{ctxt['a']['a']}-{ctxt['a']['c']}-{ctxt['a']['d']}-{ctxt['a']['f']}-{'_'.join(args)}"

@context_producer(('.a.h', str))
@context_dependencies(('.a.g', str), ('.a.c', str))
def produce_h(ctxt):
    print("ok for feeding with .a.h")
    ctxt.setdefault('a', {}).setdefault('h', 'h'+ctxt['a']['g']+ctxt['a']['c'])

@context_producer(('.a.f', str))
@context_dependencies(('.a.h', str))
def produce_f_cyclic(ctxt):
    print("ok for feeding with .a.f")
    ctxt['a']['f'] = f"ffff-{ctxt['a']['h']}"

# mostly complicated because of cycle in the graph, one is expected to fix the issue, not to ignore it (above for test)
@context_producer(('.a.g2', str))
@context_dependencies(('.a.a', str), ('.a.c', int), ('.a.d', str), ('.a.i', str))
def big_consumer_for_acyclic_dep(ctxt, *args):
    ctxt['a']['g2'] = f"{ctxt['a']['a']}-{ctxt['a']['c']}-{ctxt['a']['d']}-{ctxt['a']['i']}-{'_'.join(args)}"
    return ctxt['a']['g2']

@context_producer(('.a.i', str))
@context_dependencies(('.a.a', str))
def produce_f_acyclic(ctxt):
    print("ok for feeding with .a.i")
    ctxt['a']['i'] = f"ffff-{ctxt['a']['a']}"

def test5():
    print(big_consumer_for_cyclic_dep())

def test6():
    print(big_consumer_for_acyclic_dep('ok'))


# now test the multithread aspect (both on context and graphs)
def todo_in_not_main_thread(*args):
    # print("Registering only at start of thread")
    @context_producer(('.a.j', str))
    @context_dependencies(('.a.i', str))
    def produce_j(ctxt):
        print("ok for feeding with .a.j in thread")
        ctxt['a']['j'] = f"JJJJJ in thread -> {ctxt['a']['i']}"
    @context_producer(('.a.k', str))
    @context_dependencies(('.a.j', str))
    def produce_k(ctxt, *args):
        print("ok for feeding with .a.k in thread")
        ctxt['a']['k'] = f"kkk in thread ({ctxt['a']['j']}) + {args}"

    from core.core30_context.context import current_ctxt
    produce_k(*args)
    print(current_ctxt())


def todo_in_main_thread():
    @context_producer(('.a.j', str))
    @context_dependencies(('.a.g2', str))
    def produce_j(ctxt):
        print("ok for feeding with .a.j in main")
        ctxt['a']['j'] = f"JJJJJ in main -> {ctxt['a']['g2']}"

    from core.core30_context.context import current_ctxt
    from time import sleep
    produce_j()
    produce_j()
    sleep(0.1)
    produce_j()
    print(current_ctxt())


def test7():
    from core.core30_context.context import current_ctxt, copy_context

    def modify_something_in_context():
        ctxt = current_ctxt()  # important: do not forget it unless you want a global failure
        print("Before modifying in context")
        print(ctxt)
        ctxt['bougie'] = 'baboin'
        print("After modifying in context")
        print(ctxt)

    c = copy_context()
    c.run(modify_something_in_context)

    print("After in main context, does it has bougie? Should not")
    ctxt = current_ctxt()
    print(ctxt)


def test8():
    print("AT BEGIN IN MAIN")
    print(ThreadSafeDependencyManager._global_context_dependencies_graph)
    print(ThreadSafeDependencyManager._global_context_nodes.keys())
    print(ThreadSafeDependencyManager._incontext_dependencies_graph.get())
    print(ThreadSafeDependencyManager._incontext_nodes.get().keys())

    ctxt_cpy = copy_context()

    def add_new_producers_consumers():
        print("AT BEGIN IN OTHER CONTEXT (should equal main)")
        print(ThreadSafeDependencyManager._global_context_dependencies_graph)
        print(ThreadSafeDependencyManager._global_context_nodes.keys())
        print(ThreadSafeDependencyManager._incontext_dependencies_graph.get())
        print(ThreadSafeDependencyManager._incontext_nodes.get().keys())

        @context_producer(('.test.incontext', str))
        @context_dependencies(('.a.a', str))
        def useless_in_context(ctxt):
            print(f"Useless there: {ctxt}")

    def end_the_print():
        print("AT END IN OTHER CONTEXT")
        print(ThreadSafeDependencyManager._global_context_dependencies_graph)
        print(ThreadSafeDependencyManager._global_context_nodes.keys())
        print(ThreadSafeDependencyManager._incontext_dependencies_graph.get())
        print(ThreadSafeDependencyManager._incontext_nodes.get().keys())

    ctxt_cpy.run(add_new_producers_consumers)

    @context_producer(('.test.inmaincontext', str))
    def useless_in_main(ctxt):
        print(f"Useless there in main: {ctxt}")

    @context_dependencies(('.a.a', str))
    def useless_in_main2(ctxt):
        print(f"Useless there in main: {ctxt}")

    ctxt_cpy.run(end_the_print)

    print("AT END IN MAIN (should equal main)")
    print(ThreadSafeDependencyManager._global_context_dependencies_graph)
    print(ThreadSafeDependencyManager._global_context_nodes.keys())
    print(ThreadSafeDependencyManager._incontext_dependencies_graph.get())
    print(ThreadSafeDependencyManager._incontext_nodes.get().keys())


if __name__ == '__main__':
    test1()
    try:
        test2()
    except AssertionError:
        print('Test2 ok (unable to reach b as not produced)')
    try:
        test3()
    except AssertionError:
        print('Test3 ok (incompatible types)')
    test4()
    try:
        test5()
    except AssertionError:
        print('Test5 ok (cyclic dependency)')
    test6()

    import threading
    t = threading.Thread(target=todo_in_not_main_thread, args=(3,))
    t.start()

    import time
    time.sleep(0.5)
    todo_in_main_thread()
    t.join()

    test7()
    test8()
