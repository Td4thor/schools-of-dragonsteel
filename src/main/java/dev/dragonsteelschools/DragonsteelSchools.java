package dev.dragonsteelschools;

import com.mojang.logging.LogUtils;
import dev.dragonsteelschools.cauldron.ModCauldronInteractions;
import dev.dragonsteelschools.config.DSConfig;
import dev.dragonsteelschools.item.SchoolTiers;
import dev.dragonsteelschools.network.DSNetwork;
import dev.dragonsteelschools.registry.ModBlocks;
import dev.dragonsteelschools.registry.ModItems;
import dev.dragonsteelschools.registry.ModRegistries;
import dev.dragonsteelschools.school.SchoolSteel;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.fml.ModLoadingContext;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.config.ModConfig;
import net.minecraftforge.fml.event.config.ModConfigEvent;
import net.minecraftforge.fml.event.lifecycle.FMLCommonSetupEvent;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import org.slf4j.Logger;

import java.util.List;

/**
 * Dragonsteel for every school of magic. Holy and Ender first.
 *
 * <p>Flow: Dragon's Breath bottles fill a cauldron; any spell of a school cast at it brews that school's dragon blood;
 * iron and school blood in an Ice and Fire dragon forge are tempered by a dragon's breath (an Ice and Fire recipe);
 * the school's Apex spell cast at the forge finishes every piece of tempered steel into dragonsteel.
 */
@Mod(DragonsteelSchools.MODID)
public final class DragonsteelSchools {
    public static final String MODID = "dragonsteel_schools";
    public static final Logger LOG = LogUtils.getLogger();

    public DragonsteelSchools() {
        IEventBus modBus = FMLJavaModLoadingContext.get().getModEventBus();
        // Tiers must be registered with Forge's tier sorting before any item uses them.
        SchoolTiers.of(SchoolSteel.HOLY);
        ModBlocks.BLOCKS.register(modBus);
        ModItems.ITEMS.register(modBus);
        ModRegistries.EFFECTS.register(modBus);
        ModRegistries.RECIPE_TYPES.register(modBus);
        ModRegistries.RECIPE_SERIALIZERS.register(modBus);
        ModRegistries.TABS.register(modBus);
        ModLoadingContext.get().registerConfig(ModConfig.Type.COMMON, DSConfig.SPEC);
        modBus.addListener(this::commonSetup);
        modBus.addListener((ModConfigEvent.Loading e) -> DSConfig.onReload());
        modBus.addListener((ModConfigEvent.Reloading e) -> DSConfig.onReload());
    }

    private void commonSetup(FMLCommonSetupEvent event) {
        DSNetwork.register();
        event.enqueueWork(ModCauldronInteractions::bootstrap);
        for (String mod : List.of("irons_spellbooks", "iceandfire", "ice_and_fire_spellbooks", "grandsigil")) {
            if (ModList.get().isLoaded(mod)) {
                LOG.info("[DragonsteelSchools/runtime] loaded {} {}", mod,
                        ModList.get().getModContainerById(mod).map(c -> c.getModInfo().getVersion().toString()).orElse("?"));
            } else {
                LOG.info("[DragonsteelSchools/runtime] absent {}", mod);
            }
        }
    }
}
