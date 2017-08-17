# coding=utf-8
import importlib

handlers = []
handler_names = ["auth", "user", ]


def _generate_handler_patterns(root_module, handler_names):
    for name in handler_names:
        module = importlib.import_module(".%s" % name, root_module)
        module_hanlders = getattr(module, "handlers", None)
        if module_hanlders:
            for handler in module_hanlders:
                try:
                    handlers.append(handler)
                except IndexError:
                    pass

_generate_handler_patterns("xiaodi.handlers", handler_names)
