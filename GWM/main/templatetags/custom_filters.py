from django import template
from decimal import Decimal
import locale

register = template.Library()

@register.filter
def currency(value):
    """
    Format a number as a Brazilian Real currency (R$ X,XX)
    """
    try:
        # Store original locale
        old_locale = locale.getlocale(locale.LC_NUMERIC)
        
        # Set locale to Brazilian Portuguese
        locale.setlocale(locale.LC_NUMERIC, 'pt_BR.UTF-8')
        
        # Convert to decimal if it's a string
        if isinstance(value, str):
            try:
                value = Decimal(value.replace('R$', '').replace('.', '').replace(',', '.').strip())
            except:
                return f"R$ 0,00"
        
        # Format the value
        formatted = locale.currency(float(value), grouping=True, symbol='R$')
        
        # Reset to original locale
        locale.setlocale(locale.LC_NUMERIC, old_locale)
        
        return formatted
    except:
        # Fallback formatting if locale settings fail
        if value is None:
            return "R$ 0,00"
            
        try:
            value = float(value)
            integer_part = int(value)
            decimal_part = int(round((value - integer_part) * 100))
            
            formatted_integer = "{:,}".format(integer_part).replace(",", ".")
            return f"R$ {formatted_integer},{decimal_part:02d}"
        except:
            return f"R$ 0,00"

@register.filter
def millions(value):
    """
    Format a number as millions (X,XX milhões)
    """
    try:
        # Convert to float if it's a string
        if isinstance(value, str):
            try:
                value = float(value.replace('R$', '').replace('.', '').replace(',', '.').strip())
            except:
                return "0,00 milhões"
        
        # Convert to millions
        value_in_millions = float(value) / 1000000
        
        # Format the value with 2 decimal places
        integer_part = int(value_in_millions)
        decimal_part = int(round((value_in_millions - integer_part) * 100))
        
        return f"{integer_part},{decimal_part:02d} milhões"
    except:
        return "0,00 milhões"

@register.filter
def make_float(value):
    """Convert a string to a float."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

@register.filter
def mul(value, arg):
    """Multiply the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Divide the value by the argument."""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def absolute(value):
    """Return the absolute value."""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """
    Calculate percentage of a value relative to a total.
    Returns an integer percentage value without the % sign.
    """
    try:
        if float(total) > 0:
            percentage = (float(value) / float(total)) * 100
            return int(round(percentage))
        return 0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0 