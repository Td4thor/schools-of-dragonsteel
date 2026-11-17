package dev.dragonsteelschools.compat.jei;

import io.redspace.ironsspellbooks.api.spells.AbstractSpell;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;

import java.util.List;

/** Drawing helpers shared by the categories. */
final class JeiDraw {
    private JeiDraw() {
    }

    /** An Iron's Spells spell icon (16 x 16). */
    static void spellIcon(GuiGraphics graphics, AbstractSpell spell, int x, int y) {
        graphics.blit(spell.getSpellIconResource(), x, y, 0, 0, 16, 16, 16, 16);
    }

    /** Text wrapped to {@code width}; returns the y below the last line. */
    static int wrapped(GuiGraphics graphics, Font font, Component text, int x, int y, int width, int color) {
        List<FormattedCharSequence> lines = font.split(text, width);
        for (FormattedCharSequence line : lines) {
            graphics.drawString(font, line, x, y, color, false);
            y += font.lineHeight + 1;
        }
        return y;
    }

    static boolean inside(double mouseX, double mouseY, int x, int y, int size) {
        return mouseX >= x && mouseX < x + size && mouseY >= y && mouseY < y + size;
    }
}
