from cement import App, TestApp, init_defaults
from cement.core.exc import CaughtSignal
from .core.exc import BanyanError
from .controllers.base import Base
from .controllers.services import ServiceController
from .controllers.roles import RoleController
from .controllers.policies import PolicyController
from .api import BanyanApiClient

# configuration defaults
CONFIG = init_defaults('banyan')
CONFIG['banyan']['api_url'] = BanyanApiClient.DEFAULT_API_URL
CONFIG['banyan']['refresh_token'] = None


def extend_client(app: App) -> None:
    api_url = app.config.get('banyan', 'api_url')
    refresh_token = app.config.get('banyan', 'refresh_token')
    client = BanyanApiClient(api_url, refresh_token, debug=app.debug)
    app.extend('client', client)


class MyApp(App):
    """Banyan CLI primary application."""

    class Meta:
        label = 'banyan'

        # configuration defaults
        config_defaults = CONFIG

        # call sys.exit() on close
        exit_on_close = True

        # load additional framework extensions
        extensions = [
            # 'yaml',
            'colorlog',
            'json',
            'tabulate',
            # 'scrub',
            'print',
            # 'jinja2',
        ]

        hooks = [
            ('post_setup', extend_client)
        ]

        # configuration handler
        # config_handler = 'yaml'

        # configuration file suffix
        # config_file_suffix = '.yml'

        # set the log handler
        log_handler = 'colorlog'

        # set the output handler
        output_handler = 'tabulate'

        # register handlers
        handlers = [
            Base,
            ServiceController,
            RoleController,
            PolicyController
        ]


class MyAppTest(TestApp, MyApp):
    """A sub-class of MyApp that is better suited for testing."""

    class Meta:
        label = 'banyan'


def main():
    with MyApp() as app:
        try:
            app.run()

        except AssertionError as e:
            print('AssertionError > %s' % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback
                traceback.print_exc()

        except BanyanError as e:
            print('BanyanError > %s' % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback
                traceback.print_exc()

        except CaughtSignal as e:
            # Default Cement signals are SIGINT and SIGTERM, exit 0 (non-error)
            print('\n%s' % e)
            app.exit_code = 0


if __name__ == '__main__':
    main()