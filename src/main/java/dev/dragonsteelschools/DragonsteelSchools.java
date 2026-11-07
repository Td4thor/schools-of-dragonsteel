package dev.dragonsteelschools;

import com.mojang.logging.LogUtils;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLCommonSetupEvent;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import org.slf4j.Logger;

import java.util.List;

@Mod(DragonsteelSchools.MODID)
public final class DragonsteelSchools {
    public static final String MODID = "dragonsteel_schools";
    public static final Logger LOG = LogUtils.getLogger();

    public DragonsteelSchools() {
        IEventBus modBus = FMLJavaModLoadingContext.get().getModEventBus();
        modBus.addListener(this::commonSetup);
    }

    private void commonSetup(FMLCommonSetupEvent event) {
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
