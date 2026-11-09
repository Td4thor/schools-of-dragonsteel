package dev.dragonsteelschools.apexonly;

import net.minecraftforge.fml.common.Mod;

/**
 * Ice and Fire: Schools of Dragonsteel - Apex Only. This add-on has no code of its own: the main mod checks whether it
 * is loaded and, if so, lets only the Apex spells in its config finish dragonsteel, whatever finishingRule says.
 */
@Mod(ApexOnly.MODID)
public final class ApexOnly {
    public static final String MODID = "dragonsteel_schools_apex_only";

    public ApexOnly() {
    }
}
