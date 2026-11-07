package dev.dragonsteelschools.gametest;

import dev.dragonsteelschools.DragonsteelSchools;
import io.redspace.ironsspellbooks.api.events.SpellOnCastEvent;
import io.redspace.ironsspellbooks.api.events.SpellPreCastEvent;
import io.redspace.ironsspellbooks.api.magic.MagicData;
import io.redspace.ironsspellbooks.api.registry.AttributeRegistry;
import io.redspace.ironsspellbooks.api.registry.SpellRegistry;
import io.redspace.ironsspellbooks.api.spells.AbstractSpell;
import io.redspace.ironsspellbooks.api.spells.CastSource;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Container;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;
import net.minecraftforge.registries.ForgeRegistries;

import java.util.concurrent.atomic.AtomicLong;
import java.util.function.Consumer;

/** Spike: proves the three risky links before any feature work. */
@GameTestHolder(DragonsteelSchools.MODID)
@PrefixGameTestTemplate(false)
public final class SpikeGameTests {
    private SpikeGameTests() {
    }

    @GameTest(template = "platform", timeoutTicks = 100)
    public static void spike_forge_assembles_and_takes_breath(GameTestHelper helper) {
        BlockPos core = new BlockPos(7, 3, 7);
        ForgeFixtures.build(helper, core, "fire", Direction.NORTH);
        helper.runAfterDelay(10, () -> {
            // Ice and Fire 2.1.13 swaps the core block the wrong way round (setState(prevAssembled)), so an assembled
            // forge keeps the "_disabled" core. The block id says nothing; only the block entity knows.
            ResourceLocation id = ForgeRegistries.BLOCKS.getKey(helper.getBlockState(core).getBlock());
            BlockEntity be = helper.getBlockEntity(core);
            helper.assertTrue(ForgeFixtures.assembled(be), "forge reports itself assembled; core block " + id);
            helper.assertTrue(be instanceof Container c && c.getContainerSize() == 3, "core is a 3-slot container: " + be);
            helper.assertTrue(ForgeFixtures.flameTimer(be) == 0, "cold forge timer is 0");
            ForgeFixtures.breathe(helper, core.relative(Direction.NORTH));
            int timer = ForgeFixtures.flameTimer(be);
            helper.assertTrue(timer > 0, "breath through the input sets the core's flame timer, was " + timer);
            DragonsteelSchools.LOG.info("[spike] assembled core {} container size 3, flame timer after breath {}", id, timer);
            helper.succeed();
        });
    }

    @GameTest(template = "platform", timeoutTicks = 260)
    public static void spike_reckoning_long_cast_fires_on_cast_after_windup(GameTestHelper helper) {
        ServerPlayer caster = TestPlayers.create(helper);
        caster.moveTo(helper.absoluteVec(new net.minecraft.world.phys.Vec3(7.5, 2, 2.5)));
        caster.getAttribute(AttributeRegistry.MAX_MANA.get()).setBaseValue(5000);
        MagicData.getPlayerMagicData(caster).setMana(5000);
        AbstractSpell spell = SpellRegistry.getSpell(new ResourceLocation("grandsigil", "reckoning"));
        helper.assertTrue(spell != SpellRegistry.none(), "Reckoning is registered");
        AtomicLong pre = new AtomicLong(-1);
        AtomicLong on = new AtomicLong(-1);
        Consumer<SpellPreCastEvent> preListener = e -> {
            if (e.getEntity() == caster) pre.set(helper.getTick());
        };
        Consumer<SpellOnCastEvent> onListener = e -> {
            if (e.getEntity() == caster) on.set(helper.getTick());
        };
        MinecraftForge.EVENT_BUS.addListener(preListener);
        MinecraftForge.EVENT_BUS.addListener(onListener);
        boolean started = spell.attemptInitiateCast(ItemStack.EMPTY, 1, helper.getLevel(), caster, CastSource.SPELLBOOK, true, "mainhand");
        helper.assertTrue(started, "Reckoning cast starts");
        helper.runAfterDelay(200, () -> {
            MinecraftForge.EVENT_BUS.unregister(preListener);
            MinecraftForge.EVENT_BUS.unregister(onListener);
            TestPlayers.remove(caster);
            helper.assertTrue(pre.get() >= 0, "SpellPreCastEvent fired");
            helper.assertTrue(on.get() >= 0, "SpellOnCastEvent fired");
            long windup = on.get() - pre.get();
            DragonsteelSchools.LOG.info("[spike] Reckoning pre-cast at {} on-cast at {} (windup {} ticks)", pre.get(), on.get(), windup);
            helper.assertTrue(windup >= 90, "OnCast fires after the 5-second windup, windup was " + windup);
            helper.succeed();
        });
    }
}
