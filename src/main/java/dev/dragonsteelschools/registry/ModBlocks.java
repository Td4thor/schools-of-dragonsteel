package dev.dragonsteelschools.registry;

import dev.dragonsteelschools.DragonsteelSchools;
import dev.dragonsteelschools.cauldron.ModCauldronInteractions;
import dev.dragonsteelschools.cauldron.SchoolCauldronBlock;
import dev.dragonsteelschools.school.SchoolSteel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LayeredCauldronBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

import java.util.EnumMap;
import java.util.Map;

public final class ModBlocks {
    public static final DeferredRegister<Block> BLOCKS = DeferredRegister.create(ForgeRegistries.BLOCKS, DragonsteelSchools.MODID);

    public static final RegistryObject<Block> BREATH_CAULDRON = BLOCKS.register("dragons_breath_cauldron",
            () -> new SchoolCauldronBlock(null, BlockBehaviour.Properties.copy(Blocks.CAULDRON).lightLevel(state -> 3),
                    ModCauldronInteractions.BREATH));

    public static final Map<SchoolSteel, RegistryObject<Block>> BLOOD_CAULDRON = new EnumMap<>(SchoolSteel.class);

    static {
        for (SchoolSteel school : SchoolSteel.values()) {
            BLOOD_CAULDRON.put(school, BLOCKS.register(school.id() + "_dragon_blood_cauldron",
                    () -> new SchoolCauldronBlock(school, BlockBehaviour.Properties.copy(Blocks.CAULDRON)
                            .lightLevel(state -> school == SchoolSteel.HOLY
                                    ? 6 + 3 * state.getValue(LayeredCauldronBlock.LEVEL)
                                    : 2 + state.getValue(LayeredCauldronBlock.LEVEL)),
                            ModCauldronInteractions.blood(school))));
        }
    }

    private ModBlocks() {
    }
}
