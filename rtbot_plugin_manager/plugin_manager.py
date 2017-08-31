import re
import imp

class PluginLoadingError(Exception):
    pass


class PluginRepository(dict):
    pass

find_class_name = re.compile(r'''class\s+([^(:]+)''')


class PluginManager:
    def __init__(self, class_selector=None):
        """

        :param class_selector: A callable that, given a class object from the module, will return whether that class
                               should be instantiated as the module's plugin.
        """
        self._repository = PluginRepository()

    @property
    def repository(self):
        return self._repository

    def load_plugin_from_string(self, code_module):
        plugin_id = find_class_name.search(code_module)
        my_module = imp.new_module('mymodule')
        exec(code_module, my_module.__dict__)
        self._repository[plugin_id] = my_module.SimplePlugin()
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
        for plugin_id, plugin in self._repository:
            callee(plugin)

    async def fire_event_async(self, callee):
        for plugin_id, plugin in self._repository:
            await callee(plugin)
