"""
Pine Indicator Class
"""
from typing import Dict, Any, Optional

class PineIndicator:
    """
    Class representing a TradingView Pine Script indicator.
    """
    def __init__(self, options: Dict[str, Any]):
        """
        Initialize the Pine indicator.

        Args:
            options: Indicator options and configuration.
        """
        self._options = options
        self._type = 'Script@tv-scripting-101!'

    @property
    def pine_id(self) -> str:
        """Get the indicator's Pine ID."""
        return self._options.get('pineId', '')

    @property
    def pine_version(self) -> str:
        """Get the indicator's Pine version."""
        return self._options.get('pineVersion', '')

    @property
    def description(self) -> str:
        """Get the indicator's description."""
        return self._options.get('description', '')

    @property
    def short_description(self) -> str:
        """Get the indicator's short description."""
        return self._options.get('shortDescription', '')

    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the indicator's input parameters."""
        return self._options.get('inputs', {})

    @property
    def plots(self) -> Dict[str, str]:
        """Get the indicator's plot configurations."""
        return self._options.get('plots', {})

    @property
    def type(self) -> str:
        """Get the indicator's type."""
        return self._type

    def set_type(self, type: str = 'Script@tv-scripting-101!') -> None:
        """
        Set the indicator's type.

        Args:
            type: The indicator type string.
        """
        self._type = type

    @property
    def script(self) -> str:
        """Get the indicator's script content."""
        return self._options.get('script', '')

    def set_option(self, key: str, value: Any) -> None:
        """
        Set an indicator option (input parameter).

        Args:
            key: The key of the option to set.
            value: The value to assign to the option.
        """
        prop_id = ''

        # Search for input parameters
        if f'in_{key}' in self._options['inputs']:
            prop_id = f'in_{key}'
        elif key in self._options['inputs']:
            prop_id = key
        else:
            # Find by inline name or internalID
            for input_id, input_data in self._options['inputs'].items():
                if input_data.get('inline') == key or input_data.get('internalID') == key:
                    prop_id = input_id
                    break

        if prop_id and prop_id in self._options['inputs']:
            input_data = self._options['inputs'][prop_id]

            # Type validation
            types = {
                'bool': bool,
                'integer': int,
                'float': float,
                'text': str
            }

            if input_data['type'] in types:
                if not isinstance(value, types[input_data['type']]):
                    raise TypeError(f"Input '{input_data['name']}' ({prop_id}) must be a {types[input_data['type']].__name__}!")

            # Options value validation
            if 'options' in input_data and value not in input_data['options']:
                raise ValueError(f"Input '{input_data['name']}' ({prop_id}) must be one of these values: {input_data['options']}")

            input_data['value'] = value
        else:
            raise KeyError(f"Input '{key}' not found ({prop_id}).")
