package dev.dragonsteelschools.cauldron;

import dev.dragonsteelschools.registry.ModBlocks;
import dev.dragonsteelschools.registry.ModItems;
import dev.dragonsteelschools.school.SchoolSteel;
import net.minecraft.core.cauldron.CauldronInteraction;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.stats.Stats;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemUtils;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.LayeredCauldronBlock;
import net.minecraft.world.level.gameevent.GameEvent;

import java.util.EnumMap;
import java.util.Map;
import java.util.function.Supplier;

/**
 * Bottle interactions, in vanilla's style: a bottle of Dragon's Breath pours one level into an empty cauldron or a
 * breath cauldron; a glass bottle draws one level back out. School blood works the same way. Buckets behave as on
 * any vanilla cauldron (water, lava and powder snow replace the contents).
 */
public final class ModCauldronInteractions {
    public static final Map<Item, CauldronInteraction> BREATH = CauldronInteraction.newInteractionMap();
    private static final Map<SchoolSteel, Map<Item, CauldronInteraction>> BLOOD = new EnumMap<>(SchoolSteel.class);

    static {
        for (SchoolSteel school : SchoolSteel.values()) {
            BLOOD.put(school, CauldronInteraction.newInteractionMap());
        }
    }

    private ModCauldronInteractions() {
    }

    public static Map<Item, CauldronInteraction> blood(SchoolSteel school) {
        return BLOOD.get(school);
    }

    /** Runs on both sides during common setup, after items and blocks exist. */
    public static void bootstrap() {
        Block breathCauldron = ModBlocks.BREATH_CAULDRON.get();
        CauldronInteraction.EMPTY.put(Items.DRAGON_BREATH, pour(breathCauldron));
        BREATH.put(Items.DRAGON_BREATH, topUp());
        BREATH.put(Items.GLASS_BOTTLE, draw(() -> new ItemStack(Items.DRAGON_BREATH)));
        CauldronInteraction.addDefaultInteractions(BREATH);

        for (SchoolSteel school : SchoolSteel.values()) {
            Item blood = ModItems.BLOOD.get(school).get();
            Map<Item, CauldronInteraction> map = BLOOD.get(school);
            CauldronInteraction.EMPTY.put(blood, pour(ModBlocks.BLOOD_CAULDRON.get(school).get()));
            map.put(blood, topUp());
            map.put(Items.GLASS_BOTTLE, draw(() -> new ItemStack(blood)));
            CauldronInteraction.addDefaultInteractions(map);
        }
    }

    /** Pours a bottle into an empty cauldron, making a level-1 cauldron of {@code target}. */
    private static CauldronInteraction pour(Block target) {
        return (state, level, pos, player, hand, stack) -> {
            if (!level.isClientSide) {
                Item item = stack.getItem();
                player.setItemInHand(hand, ItemUtils.createFilledResult(stack, player, new ItemStack(Items.GLASS_BOTTLE)));
                player.awardStat(Stats.USE_CAULDRON);
                player.awardStat(Stats.ITEM_USED.get(item));
                level.setBlockAndUpdate(pos, target.defaultBlockState());
                level.playSound(null, pos, SoundEvents.BOTTLE_EMPTY, SoundSource.BLOCKS, 1.0F, 1.0F);
                level.gameEvent(null, GameEvent.FLUID_PLACE, pos);
            }
            return InteractionResult.sidedSuccess(level.isClientSide);
        };
    }

    /** Pours one more bottle of the same contents in, up to three levels. */
    private static CauldronInteraction topUp() {
        return (state, level, pos, player, hand, stack) -> {
            int current = state.getValue(LayeredCauldronBlock.LEVEL);
            if (current >= LayeredCauldronBlock.MAX_FILL_LEVEL) {
                return InteractionResult.PASS;
            }
            if (!level.isClientSide) {
                Item item = stack.getItem();
                player.setItemInHand(hand, ItemUtils.createFilledResult(stack, player, new ItemStack(Items.GLASS_BOTTLE)));
                player.awardStat(Stats.USE_CAULDRON);
                player.awardStat(Stats.ITEM_USED.get(item));
                level.setBlockAndUpdate(pos, state.setValue(LayeredCauldronBlock.LEVEL, current + 1));
                level.playSound(null, pos, SoundEvents.BOTTLE_EMPTY, SoundSource.BLOCKS, 1.0F, 1.0F);
                level.gameEvent(null, GameEvent.FLUID_PLACE, pos);
            }
            return InteractionResult.sidedSuccess(level.isClientSide);
        };
    }

    /** Draws one level into a glass bottle. */
    private static CauldronInteraction draw(Supplier<ItemStack> result) {
        return (state, level, pos, player, hand, stack) -> {
            if (!level.isClientSide) {
                Item item = stack.getItem();
                player.setItemInHand(hand, ItemUtils.createFilledResult(stack, player, result.get()));
                player.awardStat(Stats.USE_CAULDRON);
                player.awardStat(Stats.ITEM_USED.get(item));
                LayeredCauldronBlock.lowerFillLevel(state, level, pos);
                level.playSound(null, pos, SoundEvents.BOTTLE_FILL, SoundSource.BLOCKS, 1.0F, 1.0F);
                level.gameEvent(null, GameEvent.FLUID_PICKUP, pos);
            }
            return InteractionResult.sidedSuccess(level.isClientSide);
        };
    }
}
