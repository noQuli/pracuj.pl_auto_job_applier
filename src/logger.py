import logging
import threading
import inspect

class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    RESET = "\033[0m"

class SingletonLogger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize(*args, **kwargs)
        return cls._instance

    def _initialize(self, level=logging.DEBUG):
        self.logger = logging.getLogger("SingletonLogger")
        self.logger.setLevel(level)
        self.logger.propagate = False

        if not self.logger.handlers:
            formatter = self._get_colored_formatter()

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def _get_colored_formatter(self):
        class ColoredFormatter(logging.Formatter):
            def format(self, record):
                # Find the correct frame that contains the actual caller
                frame = inspect.currentframe()
                try:
                    # Go up the stack to find the actual calling code
                    # Adjust this number based on your needs
                    depth = 0
                    while frame:
                        filename = frame.f_code.co_filename
                        # Skip internal logging and this formatter code
                        if not filename.endswith(('logging/__init__.py', 'logging\\__init__.py')):
                            if 'format' not in frame.f_code.co_name and '<' not in filename:
                                module = inspect.getmodule(frame)
                                module_name = module.__name__ if module else 'unknown'
                                
                                # Get class name if called from a method
                                class_name = ''
                                if 'self' in frame.f_locals:
                                    class_name = frame.f_locals['self'].__class__.__name__
                                elif 'cls' in frame.f_locals:
                                    class_name = frame.f_locals['cls'].__name__
                                
                                function_name = frame.f_code.co_name
                                
                                # Build caller name
                                if class_name:
                                    caller_name = f"{module_name}.{class_name}.{function_name}"
                                else:
                                    caller_name = f"{module_name}.{function_name}"
                                
                                record.name = caller_name
                                break
                        frame = frame.f_back
                        depth += 1
                        if depth > 10:  # Prevent infinite loop
                            break
                finally:
                    del frame  # Prevent reference cycles

                # Apply colors based on log level
                color = Colors.WHITE
                if record.levelno == logging.DEBUG:
                    color = Colors.CYAN
                elif record.levelno == logging.INFO:
                    color = Colors.GREEN
                elif record.levelno == logging.WARNING:
                    color = Colors.YELLOW
                elif record.levelno == logging.ERROR:
                    color = Colors.RED
                elif record.levelno == logging.CRITICAL:
                    color = Colors.PURPLE

                original_format = super().format(record)
                colored_format = f"{color}{original_format}{Colors.RESET}"
                return colored_format

        return ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - line:%(lineno)d - %(message)s')

    def set_level(self, level):
        self.logger.setLevel(level)

    def get_logger(self):
        return self.logger

    def remove_logger(self):
        """Remove all handlers from the logger."""
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

# Example classes for testing

def example_method():
    logger = SingletonLogger().get_logger()
    logger.debug("This is a debug message from ExampleClass.example_method")
    logger.info("This is an info message from ExampleClass.example_method")
    logger.warning("This is a warning message from ExampleClass.example_method")
    logger.error("This is an error message from ExampleClass.example_method")
    logger.critical("This is a critical message from ExampleClass.example_method")

class ExampleClass1:
    def __init__(self):
        self.logger = SingletonLogger().get_logger()
    
    def example_method(self):
        self.logger.debug("This is a debug message from ExampleClass1.example_method")
        self.logger.info("This is an info message from ExampleClass1.example_method")

# Test the logger
if __name__ == "__main__":
    import sys
    
    # Set initial level
    SingletonLogger().set_level(logging.DEBUG)
    
    print("=== Testing ExampleClass ===")
    example_method()

    print("\n=== Testing ExampleClass1 ===")
    example1 = ExampleClass1()
    example1.example_method()

    print("\n=== Changing level to INFO ===")
    SingletonLogger().set_level(logging.INFO)
    example1.example_method()  # Only INFO and above will show
    
    print("\n=== Removing logger ===")
    SingletonLogger().remove_logger()