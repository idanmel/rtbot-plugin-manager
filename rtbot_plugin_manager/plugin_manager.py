import re
import imp


class PluginLoadingError(Exception):
    pass


class PluginRepository(dict):
    pass


re_class_name = re.compile(r'''class\s+([^(:]+)''')
re_class_father = re.compile(r'''class\s+[^(:]+\(([^)]+)''')


def parse_classes(text):
    """

    :param text: a string that represents a module
    :return: a string that represents a class
    """
    a_class = list()
    for line in text.splitlines():
        if line.startswith("class "):
            if a_class:
                yield '\n'.join(a_class)
                a_class = list()
            a_class.append(line)
        if a_class and line.startswith(" "):
            a_class.append(line)
    if a_class:
        yield '\n'.join(a_class)


class PluginManager:
    def __init__(self, class_selector=None):
        """

        :param class_selector: A callable that, given a class object from the module, will return whether that class
                               should be instantiated as the module's plugin.
        """
        self._repository = PluginRepository()
        self.class_selector = class_selector

    @property
    def repository(self):
        return self._repository

    def load_plugin_from_string(self, module_code):
        for class_code in parse_classes(module_code):
            if self.class_selector:
                match = re_class_father.search(class_code)
                if match:
                    if self.class_selector != match.group(1):
                        continue
                else:
                    continue
            if self.class_selector:
                class_code = class_code.replace(self.class_selector, '')
            plugin_id = re_class_name.search(class_code).group(1)
            my_module = imp.new_module('mymodule')
            exec(class_code, my_module.__dict__)
            try:
                self._repository[plugin_id] = my_module.__dict__[plugin_id]()
            except Exception as e:
                raise PluginLoadingError from e
            return plugin_id

    def load_plugin_from_file(self, filename):
        with open(filename, 'r') as f:
            plugin_code = f.read()
        return self.load_plugin_from_string(plugin_code)

    def unload_plugin(self, plugin_id):
        """
        ...

        The final state is guaranteed to be that no plugin with the given ID is loaded, independently from the return value.

        :param plugin_id:
        :return: Whether the plugin was unloaded (was loaded before and now no longer is)
        """
        del self._repository[plugin_id]
        return True

    def fire_event(self, callee):
        for plugin_id, plugin in self._repository.items():
            callee(plugin)

    async def fire_event_async(self, callee):
        for plugin_id, plugin in self._repository.items():
            await callee(plugin)
