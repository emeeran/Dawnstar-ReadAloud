#!/usr/bin/env python3
"""Get text from focused window using AT-SPI accessibility APIs.

This extracts text from the currently focused application without
any visual selection or scrolling.
"""

import sys

try:
    import pyatspi
except ImportError:
    print("pyatspi is required: pip install pyatspi")
    sys.exit(1)


# Minimum text length to consider valid (avoid window titles, labels)
MIN_TEXT_LENGTH = 1


def get_focused_text_from_cursor():
    """Get text from focused accessible object, from cursor position to end.

    Returns:
        str: Text from cursor position to end, or empty string if not found.
    """
    desktop = pyatspi.Registry.getDesktop(0)
    best_text = ""

    for app in desktop:
        if not app:
            continue
        try:
            for frame in app:
                if not frame:
                    continue
                try:
                    frame_state = frame.getState()
                    if frame_state and frame_state.contains(pyatspi.STATE_ACTIVE):
                        text = find_text_from_cursor(frame)
                        if text and len(text) > len(best_text):
                            best_text = text
                except (AttributeError, RuntimeError):
                    continue
        except (AttributeError, RuntimeError):
            continue

    return best_text


def find_text_from_cursor(obj, depth=0):
    """Recursively find text from cursor position in accessible object.

    Args:
        obj: Accessible object to search.
        depth: Current recursion depth.

    Returns:
        str: Text from cursor position, or empty string.
    """
    if depth > 25:
        return ""

    best_text = ""

    try:
        # Check if this object has text and caret
        text_iface = obj.queryText()
        if text_iface:
            caret_offset = text_iface.caretOffset
            char_count = text_iface.characterCount

            # Must have meaningful content and a valid cursor position
            if caret_offset >= 0 and char_count > MIN_TEXT_LENGTH:
                # Get text from caret to end
                text = text_iface.getText(caret_offset, char_count)
                if text and len(text) > len(best_text):
                    text_stripped = text.strip()
                    if len(text_stripped) > MIN_TEXT_LENGTH:
                        best_text = text_stripped
    except (AttributeError, RuntimeError, NotImplementedError):
        pass

    # Recursively search children for longer text
    try:
        for i in range(obj.childCount):
            child = obj.getChildAtIndex(i)
            if child:
                result = find_text_from_cursor(child, depth + 1)
                if result and len(result) > len(best_text):
                    best_text = result
    except (AttributeError, RuntimeError, IndexError):
        pass

    return best_text


def get_selected_text():
    """Get currently selected text from focused window.

    Returns:
        str: Selected text, or empty string if none.
    """
    desktop = pyatspi.Registry.getDesktop(0)

    for app in desktop:
        if not app:
            continue
        try:
            for frame in app:
                if not frame:
                    continue
                try:
                    frame_state = frame.getState()
                    if frame_state and frame_state.contains(pyatspi.STATE_ACTIVE):
                        text = find_selected_text(frame)
                        if text:
                            return text
                except (AttributeError, RuntimeError):
                    continue
        except (AttributeError, RuntimeError):
            continue

    return ""


def find_selected_text(obj, depth=0):
    """Recursively find selected text in accessible object.

    Args:
        obj: Accessible object to search.
        depth: Current recursion depth.

    Returns:
        str: Selected text, or empty string.
    """
    if depth > 25:
        return ""

    try:
        text_iface = obj.queryText()
        if text_iface:
            # Check for text selection via text interface
            n_selections = text_iface.nSelections
            if n_selections > 0:
                start, end = text_iface.getSelection(0)
                if end > start:
                    selected = text_iface.getText(start, end)
                    if selected and selected.strip():
                        return selected.strip()
    except (AttributeError, RuntimeError, NotImplementedError):
        pass

    # Check selection interface
    try:
        selection_iface = obj.querySelection()
        if selection_iface and selection_iface.nSelectedChildren > 0:
            for i in range(selection_iface.nSelectedChildren):
                child = selection_iface.getSelectedChild(i)
                try:
                    child_text = child.queryText()
                    if child_text:
                        text = child_text.getText(0, child_text.characterCount)
                        if text and text.strip():
                            return text.strip()
                except (AttributeError, RuntimeError, NotImplementedError):
                    pass
    except (AttributeError, RuntimeError, NotImplementedError):
        pass

    # Recursively search children
    try:
        for i in range(obj.childCount):
            child = obj.getChildAtIndex(i)
            if child:
                result = find_selected_text(child, depth + 1)
                if result:
                    return result
    except (AttributeError, RuntimeError, IndexError):
        pass

    return ""


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""

    if mode == "--selection":
        text = get_selected_text()
    elif mode == "--cursor":
        text = get_focused_text_from_cursor()
    else:
        # Default: try selection first, then cursor position
        text = get_selected_text()
        if not text:
            text = get_focused_text_from_cursor()

    if text:
        print(text)
