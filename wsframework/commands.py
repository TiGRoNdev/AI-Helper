# SPDX-License-Identifier: LGPL-2.1-or-later

import argparse
import logging


logger = logging.getLogger('aiohttp.server')


class ArgumentParserError(Exception):
    pass


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)

    def exit(self, status=None, message=None):
        if any([status, message]):
            logger.warning(f"ARGPARSE-EXIT: {status} - {message}")

    def set_prog(self, prog):
        self.prog = prog
        return self


class CommandArgument:
    def __init__(
            self,
            names,
            action="extend",
            nargs="+",
            help_text="need help text",
            const=4,
            type_arg=str,
            default=None,
            required=False
    ):
        if not names:
            raise ValueError("names arg must be specified")

        self.names = names
        self.action = action
        self.help = help_text
        self.required_arg = False

        if action == 'store_const':
            self.const = const
        else:
            self.nargs = nargs
            self.type = type_arg

        if default:
            self.default = default

        if required:
            self.required_arg = True


class WebSocketCommand:
    def __init__(self, handler, description, binary=False, json=False, **kwargs):
        """
        kwargs: Возможные аргументы для комманды
        """
        self.handler = handler
        self.parser = None
        self.description = description
        self.required_args = []

        if not binary and not json:
            self.parser = ArgumentParser(
                description=description,
                add_help=False
            )
            # Собственный help аргумент
            self.parser.add_argument(
                '--help',
                action='store_true'
            )

            for arg_name, arg in kwargs.items():
                if arg_name in ['binary']:
                    continue

                self.parser.add_argument(
                    *arg.names,
                    **{k: v for k, v in arg.__dict__.items() if k not in ['names', 'required_arg']}
                )
                if arg.required_arg:
                    self.required_args.append(arg_name)

