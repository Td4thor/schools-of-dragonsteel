package dev.dragonsteelschools.forge;

import dev.dragonsteelschools.config.DSConfig;
import io.redspace.ironsspellbooks.api.registry.SpellRegistry;
import io.redspace.ironsspellbooks.api.spells.AbstractSpell;
import io.redspace.ironsspellbooks.api.spells.SpellRarity;
import net.minecraftforge.fml.ModList;
import org.jetbrains.annotations.Nullable;

/**
 * Which spells finish tempered steel at a dragon forge.
 * <ul>
 *   <li>{@link #LEGENDARY} (default): any spell of the steel's school cast at Legendary rarity, plus every Apex spell in
 *   the config list. The rarity is Iron's own ({@code AbstractSpell.getRarity(level)}, 3.16.3): the top level of every
 *   spell above level 1, the top bracket of levels by Iron's rarityConfig (Heal 7-8 of 8, Sunbeam 10 of 10), and every
 *   level of a spell whose minimum rarity is Legendary (Angel Wings, Black Hole, all Eldritch spells). A spell whose top
 *   level is 1 keeps its base rarity. Wololo, a Legendary novelty, is excluded by default.</li>
 *   <li>{@link #APEX_ONLY}: only the Apex spells in the config list (Apex Arcana's by default), the original rite. The
 *   optional Apex Only add-on forces it, whatever the config says.</li>
 * </ul>
 */
public enum FinishingRule {
    LEGENDARY("legendary"),
    APEX_ONLY("apex");

    /** Mod id of the optional add-on jar that forces {@link #APEX_ONLY}. */
    public static final String APEX_ONLY_ADDON = "dragonsteel_schools_apex_only";

    private static volatile Boolean addonLoaded;
    /** The server's rule, on a client connected to one (set by RuleSyncPacket, cleared on logout). */
    private static volatile FinishingRule synced;

    private final String langSuffix;

    FinishingRule(String langSuffix) {
        this.langSuffix = langSuffix;
    }

    /** Suffix of the rule's lang keys, e.g. {@code item.dragonsteel_schools.tempered_steel.lore.legendary}. */
    public String langSuffix() {
        return langSuffix;
    }

    public static boolean addonLoaded() {
        Boolean loaded = addonLoaded;
        if (loaded == null) {
            ModList mods = ModList.get();
            if (mods == null) {
                return false;
            }
            loaded = mods.isLoaded(APEX_ONLY_ADDON);
            addonLoaded = loaded;
        }
        return loaded;
    }

    /** The rule this side enforces: the add-on wins over the config. */
    public static FinishingRule active() {
        return addonLoaded() ? APEX_ONLY : DSConfig.get(DSConfig.FINISHING_RULE);
    }

    /** The rule tooltips describe: the server's when connected to one, else this side's own. */
    public static FinishingRule forTooltip() {
        FinishingRule rule = synced;
        return rule != null ? rule : active();
    }

    public static void setSynced(@Nullable FinishingRule rule) {
        synced = rule;
    }

    /** Whether this cast finishes its school's tempered steel under {@code rule}. The school match is the caller's. */
    public static boolean finishes(String spellId, int spellLevel, FinishingRule rule) {
        if (DSConfig.isApex(spellId)) {
            return true;
        }
        if (rule != LEGENDARY || DSConfig.isLegendaryExcluded(spellId)) {
            return false;
        }
        AbstractSpell spell = SpellRegistry.getSpell(spellId);
        return spell != null && spell != SpellRegistry.none() && spell.getRarity(spellLevel) == SpellRarity.LEGENDARY;
    }
}
