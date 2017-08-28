

class PluginLoadingError(Exception):
    pass


class PluginRepository(dict):
    pass


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
        return 'new-plugin-id'

    def load_plugin_from_file(self, filename):
        return 'new-plugin-id'

    def unload_plugin(self, plugin_id):
        """
        ...

        The final state is guaranteed to be that no plugin with the given ID is loaded, independently from the return value.

        :param plugin_id:
        :return: Whether the plugin was unloaded (was loaded before and now no longer is)
        """
        return False

    def fire_event(self, callee):
        for plugin_id, plugin in self._repository:
            callee(plugin)

    async def fire_event_async(self, callee):
        for plugin_id, plugin in self._repository:
            await callee(plugin)
