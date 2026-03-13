"""Checklist multi-selección basada en curses compartida por el CLI de Hermes.

La usan tanto ``hermes tools`` como ``hermes skills`` para mostrar una lista
de elementos que se pueden activar/desactivar. Si curses no está disponible
(Windows sin curses, stdin redirigido, etc.), cae a una interfaz de texto
numerada.
"""

from typing import List, Set

from hermes_cli.colors import Colors, color


def curses_checklist(
    title: str,
    items: List[str],
    pre_selected: Set[int],
) -> Set[int]:
    """Checklist de multi-selección. Devuelve el conjunto de índices
    **seleccionados**.

    Args:
        title: texto de encabezado mostrado arriba del checklist.
        items: etiquetas que se muestran para cada fila.
        pre_selected: índices que comienzan marcados.

    Returns:
        Los índices que el usuario confirmó como marcados. Si se cancela
        (ESC/q), devuelve ``pre_selected`` sin cambios.
    """
    try:
        import curses
        selected = set(pre_selected)
        result = [None]

        def _ui(stdscr):
            curses.curs_set(0)
            if curses.has_colors():
                curses.start_color()
                curses.use_default_colors()
                curses.init_pair(1, curses.COLOR_GREEN, -1)
                curses.init_pair(2, curses.COLOR_YELLOW, -1)
                curses.init_pair(3, 8, -1)  # dim gray
            cursor = 0
            scroll_offset = 0

            while True:
                stdscr.clear()
                max_y, max_x = stdscr.getmaxyx()

                # Encabezado
                try:
                    hattr = curses.A_BOLD | (curses.color_pair(2) if curses.has_colors() else 0)
                    stdscr.addnstr(0, 0, title, max_x - 1, hattr)
                    stdscr.addnstr(
                        1, 0,
                        "  ↑↓ navigate  SPACE toggle  ENTER confirm  ESC cancel",
                        max_x - 1, curses.A_DIM,
                    )
                except curses.error:
                    pass

                # Lista de elementos desplazable
                visible_rows = max_y - 3
                if cursor < scroll_offset:
                    scroll_offset = cursor
                elif cursor >= scroll_offset + visible_rows:
                    scroll_offset = cursor - visible_rows + 1

                for draw_i, i in enumerate(
                    range(scroll_offset, min(len(items), scroll_offset + visible_rows))
                ):
                    y = draw_i + 3
                    if y >= max_y - 1:
                        break
                    check = "✓" if i in selected else " "
                    arrow = "→" if i == cursor else " "
                    line = f" {arrow} [{check}] {items[i]}"

                    attr = curses.A_NORMAL
                    if i == cursor:
                        attr = curses.A_BOLD
                        if curses.has_colors():
                            attr |= curses.color_pair(1)
                    try:
                        stdscr.addnstr(y, 0, line, max_x - 1, attr)
                    except curses.error:
                        pass

                stdscr.refresh()
                key = stdscr.getch()

                if key in (curses.KEY_UP, ord("k")):
                    cursor = (cursor - 1) % len(items)
                elif key in (curses.KEY_DOWN, ord("j")):
                    cursor = (cursor + 1) % len(items)
                elif key == ord(" "):
                    selected.symmetric_difference_update({cursor})
                elif key in (curses.KEY_ENTER, 10, 13):
                    result[0] = set(selected)
                    return
                elif key in (27, ord("q")):
                    result[0] = set(pre_selected)
                    return

        curses.wrapper(_ui)
        return result[0] if result[0] is not None else set(pre_selected)

    except Exception:
        pass  # fall through to numbered fallback

    # ── Fallback de texto numerado ────────────────────────────────────────
    selected = set(pre_selected)
    print(color(f"\n  {title}", Colors.YELLOW))
    print(color("  Cambia por número, Enter para confirmar.\n", Colors.DIM))

    while True:
        for i, label in enumerate(items):
            check = "✓" if i in selected else " "
            print(f"    {i + 1:3}. [{check}] {label}")
        print()

        try:
            raw = input(color("  Número para cambiar, 's' para guardar, 'q' para cancelar: ", Colors.DIM)).strip()
        except (KeyboardInterrupt, EOFError):
            return set(pre_selected)

        if raw.lower() == "s" or raw == "":
            return selected
        if raw.lower() == "q":
            return set(pre_selected)
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(items):
                selected.symmetric_difference_update({idx})
        except ValueError:
            print(color("  Entrada no válida", Colors.DIM))
