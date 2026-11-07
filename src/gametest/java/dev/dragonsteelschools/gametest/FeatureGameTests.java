package dev.dragonsteelschools.gametest;

import dev.dragonsteelschools.DragonsteelSchools;
import dev.dragonsteelschools.forge.ForgeBatchMath;
import dev.dragonsteelschools.registry.ModBlocks;
import dev.dragonsteelschools.registry.ModItems;
import dev.dragonsteelschools.registry.ModRegistries;
import dev.dragonsteelschools.school.SchoolSteel;
import io.redspace.ironsspellbooks.api.magic.MagicData;
import io.redspace.ironsspellbooks.api.registry.AttributeRegistry;
import io.redspace.ironsspellbooks.api.registry.SpellRegistry;
import io.redspace.ironsspellbooks.api.spells.AbstractSpell;
import io.redspace.ironsspellbooks.api.spells.CastSource;
import net.minecraft.commands.arguments.EntityAnchorArgument;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Container;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Husk;
import net.minecraft.world.entity.projectile.Arrow;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LayeredCauldronBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import io.redspace.ironsspellbooks.api.events.SpellOnCastEvent;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

import java.lang.reflect.Field;
import java.util.Collection;
import java.util.List;
import java.util.concurrent.atomic.AtomicLong;
import java.util.function.Consumer;

/** The Holy/Ender proof of concept, end to end, on a real server with real survival players. */
@GameTestHolder(DragonsteelSchools.MODID)
@PrefixGameTestTemplate(false)
public final class FeatureGameTests {
    private FeatureGameTests() {
    }

    // ------------------------------------------------------------------------------------------ cauldron

    @GameTest(template = "platform", timeoutTicks = 80)
    public static void cauldron_breath_then_holy_spell_brews_holy_blood(GameTestHelper helper) {
        BlockPos pos = new BlockPos(7, 2, 9);
        helper.setBlock(pos.below(), Blocks.STONE);
        helper.setBlock(pos, Blocks.CAULDRON);
        ServerPlayer player = TestPlayers.create(helper);
        player.moveTo(helper.absoluteVec(new Vec3(7.5, 2, 5.5)));
        helper.startSequence()
                .thenExecute(() -> {
                    for (int i = 0; i < 3; i++) {
                        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.DRAGON_BREATH));
                        use(helper, player, pos);
                        helper.assertTrue(player.getMainHandItem().is(Items.GLASS_BOTTLE), "bottle " + (i + 1) + " poured, glass bottle returned");
                    }
                    BlockState full = helper.getBlockState(pos);
                    helper.assertTrue(full.is(ModBlocks.BREATH_CAULDRON.get()) && full.getValue(LayeredCauldronBlock.LEVEL) == 3,
                            "three Dragon's Breath bottles fill a breath cauldron to level 3, was " + full);
                    cast(helper, player, "irons_spellbooks:heal", pos);   // any Holy spell; Iron's completes it next tick
                })
                .thenExecuteAfter(10, () -> {
                    BlockState blood = helper.getBlockState(pos);
                    helper.assertTrue(blood.is(ModBlocks.BLOOD_CAULDRON.get(SchoolSteel.HOLY).get()) && blood.getValue(LayeredCauldronBlock.LEVEL) == 3,
                            "a Holy spell turns the breath into Holy dragon blood, was " + blood);
                    for (int i = 0; i < 3; i++) {
                        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.GLASS_BOTTLE));
                        use(helper, player, pos);
                        helper.assertTrue(player.getMainHandItem().is(ModItems.BLOOD.get(SchoolSteel.HOLY).get()), "bottle " + (i + 1) + " of Holy blood drawn");
                    }
                    helper.assertBlockPresent(Blocks.CAULDRON, pos);
                    TestPlayers.remove(player);
                })
                .thenSucceed();
    }

    @GameTest(template = "platform", timeoutTicks = 80)
    public static void cauldron_ender_spell_brews_ender_blood_and_fire_spell_does_nothing(GameTestHelper helper) {
        BlockPos pos = new BlockPos(7, 2, 9);
        helper.setBlock(pos.below(), Blocks.STONE);
        helper.setBlock(pos, ModBlocks.BREATH_CAULDRON.get().defaultBlockState().setValue(LayeredCauldronBlock.LEVEL, 2));
        ServerPlayer player = TestPlayers.create(helper);
        player.moveTo(helper.absoluteVec(new Vec3(7.5, 2, 5.5)));
        helper.startSequence()
                .thenExecute(() -> cast(helper, player, "irons_spellbooks:firebolt", pos))   // Fire has Ice and Fire's own dragonsteel
                .thenExecuteAfter(10, () -> {
                    helper.assertTrue(helper.getBlockState(pos).is(ModBlocks.BREATH_CAULDRON.get()), "a Fire spell leaves the breath alone");
                    cast(helper, player, "irons_spellbooks:evasion", pos);    // any Ender spell
                })
                .thenExecuteAfter(10, () -> {
                    BlockState blood = helper.getBlockState(pos);
                    helper.assertTrue(blood.is(ModBlocks.BLOOD_CAULDRON.get(SchoolSteel.ENDER).get()) && blood.getValue(LayeredCauldronBlock.LEVEL) == 2,
                            "an Ender spell makes Ender blood and keeps the fill level, was " + blood);
                    TestPlayers.remove(player);
                })
                .thenSucceed();
    }

    // ------------------------------------------------------------------------------------------ forge

    @GameTest(template = "platform", timeoutTicks = 200)
    public static void forge_dragon_breath_tempers_iron_with_school_blood(GameTestHelper helper) {
        BlockPos core = new BlockPos(7, 3, 7);
        ForgeFixtures.build(helper, core, "ice", Direction.NORTH);
        helper.runAfterDelay(5, () -> {
            BlockEntity be = helper.getBlockEntity(core);
            Container forge = (Container) be;
            forge.setItem(0, new ItemStack(Items.IRON_INGOT, 4));
            forge.setItem(1, new ItemStack(ModItems.BLOOD.get(SchoolSteel.HOLY).get(), 4));
            setInt(be, "cookTime", 985);   // skip 49 of the 50 seconds a real ingot takes
        });
        helper.onEachTick(() -> {
            if (helper.getTick() > 5) {
                ForgeFixtures.breathe(helper, core.relative(Direction.NORTH));
            }
        });
        helper.succeedWhen(() -> {
            Container forge = (Container) helper.getBlockEntity(core);
            ItemStack out = forge.getItem(2);
            helper.assertTrue(out.is(ModItems.TEMPERED.get(SchoolSteel.HOLY).get()), "output is tempered Holy steel, was " + out);
            helper.assertTrue(forge.getItem(0).getCount() == 3 && forge.getItem(1).getCount() == 3, "one iron and one blood used");
        });
    }

    /** Own batch: two Reckonings winding up at once (the spike's and this one) must not share a run. */
    @GameTest(template = "platform", timeoutTicks = 260, batch = "apex")
    public static void forge_holy_apex_finishes_tempered_steel_into_dragonsteel(GameTestHelper helper) {
        BlockPos core = new BlockPos(7, 3, 9);
        ForgeFixtures.build(helper, core, "fire", Direction.NORTH);
        ServerPlayer player = TestPlayers.create(helper);
        AtomicLong onCast = new AtomicLong(-1);
        Consumer<SpellOnCastEvent> listener = e -> {
            if (e.getEntity() == player) onCast.set(helper.getTick());
        };
        MinecraftForge.EVENT_BUS.addListener(listener);
        helper.runAfterDelay(5, () -> {
            Container forge = (Container) helper.getBlockEntity(core);
            forge.setItem(2, new ItemStack(ModItems.TEMPERED.get(SchoolSteel.HOLY).get(), 10));
            forge.setItem(0, new ItemStack(ModItems.TEMPERED.get(SchoolSteel.ENDER).get(), 3));   // other school: untouched
            player.moveTo(helper.absoluteVec(new Vec3(7.5, 3, 2.5)));
            helper.assertTrue(startCast(helper, player, "grandsigil:reckoning", core), "Reckoning starts");   // 5 s windup
        });
        // Look at the sky during the windup: the forge aimed at when the cast began still counts.
        helper.runAfterDelay(40, () -> player.setXRot(-85.0F));
        helper.runAfterDelay(200, () -> {
            MinecraftForge.EVENT_BUS.unregister(listener);
            TestPlayers.remove(player);
            Container forge = (Container) helper.getBlockEntity(core);
            ItemStack out = forge.getItem(2);
            helper.assertTrue(onCast.get() > 0, "Reckoning completed (SpellOnCastEvent)");
            helper.assertTrue(out.is(ModItems.INGOT.get(SchoolSteel.HOLY).get()) && out.getCount() == 10,
                    "Reckoning finished all 10 tempered Holy steel into Holy dragonsteel, output " + out + ", on-cast tick " + onCast.get());
            helper.assertTrue(forge.getItem(0).is(ModItems.TEMPERED.get(SchoolSteel.ENDER).get()) && forge.getItem(0).getCount() == 3,
                    "a Holy Apex leaves Ender steel alone, input " + forge.getItem(0));
            helper.succeed();
        });
    }

    @GameTest(template = "platform", timeoutTicks = 80)
    public static void forge_ordinary_holy_spell_does_not_finish_steel(GameTestHelper helper) {
        BlockPos core = new BlockPos(7, 3, 9);
        ForgeFixtures.build(helper, core, "fire", Direction.NORTH);
        ServerPlayer player = TestPlayers.create(helper);
        helper.startSequence()
                .thenExecuteAfter(5, () -> {
                    ((Container) helper.getBlockEntity(core)).setItem(2, new ItemStack(ModItems.TEMPERED.get(SchoolSteel.HOLY).get(), 5));
                    player.moveTo(helper.absoluteVec(new Vec3(7.5, 3, 2.5)));
                    cast(helper, player, "irons_spellbooks:heal", core);
                })
                .thenExecuteAfter(15, () -> {
                    TestPlayers.remove(player);
                    ItemStack out = ((Container) helper.getBlockEntity(core)).getItem(2);
                    helper.assertTrue(out.is(ModItems.TEMPERED.get(SchoolSteel.HOLY).get()) && out.getCount() == 5, "only an Apex spell finishes steel, output " + out);
                })
                .thenSucceed();
    }

    @GameTest(template = "platform")
    public static void forge_batch_math(GameTestHelper helper) {
        helper.assertTrue(ForgeBatchMath.finishSlot(64, 64, 1, 64) == 64, "a full stack finishes");
        helper.assertTrue(ForgeBatchMath.finishSlot(10, 64, 1, 64) == 10, "a partial stack finishes");
        helper.assertTrue(ForgeBatchMath.finishSlot(10, 5, 1, 64) == 0, "a slot larger than the remaining budget waits");
        helper.assertTrue(ForgeBatchMath.finishSlot(40, 64, 2, 64) == 0, "a result that would overflow its stack waits");
        helper.assertTrue(ForgeBatchMath.finishSlot(0, 64, 1, 64) == 0, "an empty slot does nothing");
        helper.succeed();
    }

    // ------------------------------------------------------------------------------------------ recipes

    @GameTest(template = "platform")
    public static void recipes_all_load(GameTestHelper helper) {
        var recipes = helper.getLevel().getRecipeManager();
        for (SchoolSteel school : SchoolSteel.values()) {
            String s = school.id();
            List<String> ids = new java.util.ArrayList<>(List.of("apex/" + s + "_dragonsteel_ingot",
                    "dragonforge/tempered_" + s + "_steel_fire", "dragonforge/tempered_" + s + "_steel_ice",
                    "dragonforge/tempered_" + s + "_steel_lightning", "dragonforge/" + school.staffId() + "_fire",
                    school.swordId()));
            for (String piece : List.of("helmet", "chestplate", "leggings", "boots", "pickaxe", "axe", "shovel", "hoe")) {
                ids.add(s + "_dragonsteel_" + piece);
            }
            for (String id : ids) {
                helper.assertTrue(recipes.byKey(new ResourceLocation(DragonsteelSchools.MODID, id)).isPresent(), "recipe loaded: " + id);
            }
        }
        helper.succeed();
    }

    // ------------------------------------------------------------------------------------------ gear

    /** Writes every registered id in our namespace for tools/check_assets.py to cross-check models, textures and lang. */
    @GameTest(template = "platform")
    public static void registry_dump_for_asset_check(GameTestHelper helper) {
        StringBuilder out = new StringBuilder();
        net.minecraftforge.registries.ForgeRegistries.ITEMS.getKeys().stream()
                .filter(id -> id.getNamespace().equals(DragonsteelSchools.MODID)).sorted()
                .forEach(id -> out.append("item ").append(id.getPath()).append('\n'));
        net.minecraftforge.registries.ForgeRegistries.BLOCKS.getKeys().stream()
                .filter(id -> id.getNamespace().equals(DragonsteelSchools.MODID)).sorted()
                .forEach(id -> out.append("block ").append(id.getPath()).append('\n'));
        net.minecraftforge.registries.ForgeRegistries.MOB_EFFECTS.getKeys().stream()
                .filter(id -> id.getNamespace().equals(DragonsteelSchools.MODID)).sorted()
                .forEach(id -> out.append("effect ").append(id.getPath()).append('\n'));
        try {
            java.nio.file.Files.writeString(java.nio.file.Path.of("ds_registry.txt"), out.toString());
        } catch (java.io.IOException failure) {
            throw new IllegalStateException(failure);
        }
        helper.assertTrue(out.length() > 0, "registry ids found");
        helper.succeed();
    }

    @GameTest(template = "platform")
    public static void plate_pieces_mirror_dragon_priest_stats(GameTestHelper helper) {
        int[] armour = {6, 12, 9, 6};   // head, chest, legs, feet
        ArmorItem.Type[] types = {ArmorItem.Type.HELMET, ArmorItem.Type.CHESTPLATE, ArmorItem.Type.LEGGINGS, ArmorItem.Type.BOOTS};
        for (SchoolSteel school : SchoolSteel.values()) {
            List<Item> pieces = ModItems.armorPieces(school).stream().map(r -> r.get()).toList();
            for (int i = 0; i < 4; i++) {
                ItemStack stack = new ItemStack(pieces.get(i));
                EquipmentSlot slot = types[i].getSlot();
                var mods = stack.getAttributeModifiers(slot);
                helper.assertTrue(sum(mods.get(Attributes.ARMOR)) == armour[i], school + " " + types[i] + " armour " + armour[i]);
                helper.assertTrue(sum(mods.get(Attributes.ARMOR_TOUGHNESS)) == 6, school + " toughness 6");
                helper.assertTrue(sum(mods.get(AttributeRegistry.MAX_MANA.get())) == 150, school + " +150 mana");
                helper.assertTrue(near(sum(mods.get(AttributeRegistry.SPELL_POWER.get())), 0.05), school + " +5% spell power");
                helper.assertTrue(near(sum(mods.get(school.schoolPower().get())), 0.10), school + " +10% school power");
            }
        }
        helper.succeed();
    }

    @GameTest(template = "platform", timeoutTicks = 120)
    public static void dawn_smites_undead_and_lights_unquenchable_holy_fire(GameTestHelper helper) {
        ServerPlayer player = TestPlayers.create(helper);
        player.moveTo(helper.absoluteVec(new Vec3(7.5, 1, 3.5)));
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(ModItems.SWORD.get(SchoolSteel.HOLY).get()));
        Husk struck = helper.spawn(EntityType.HUSK, new BlockPos(4, 1, 7));
        Husk burned = helper.spawn(EntityType.HUSK, new BlockPos(10, 1, 7));
        struck.setNoAi(true);
        burned.setNoAi(true);
        float before = struck.getHealth();
        struck.hurt(helper.getLevel().damageSources().playerAttack(player), 5.0F);
        float lost = before - struck.getHealth();
        helper.assertTrue(lost > 12.0F, "Dawn adds +8 against undead (5 + 8, less 2 natural armour), lost " + lost);

        player.attack(burned);
        helper.assertTrue(burned.hasEffect(ModRegistries.HOLY_FIRE.get()), "a Dawn hit lights holy fire");
        helper.setBlock(new BlockPos(10, 1, 7), Blocks.WATER);
        float afterHit = burned.getHealth();
        helper.runAfterDelay(55, () -> {
            TestPlayers.remove(player);
            helper.assertTrue(burned.isInWater(), "the husk stands in water");
            helper.assertTrue(burned.hasEffect(ModRegistries.HOLY_FIRE.get()), "water does not quench holy fire");
            float burnt = afterHit - burned.getHealth();
            helper.assertTrue(burnt >= 3.9F, "two seconds of holy fire at double damage against undead, lost " + burnt);
            helper.succeed();
        });
    }

    @GameTest(template = "platform", timeoutTicks = 40)
    public static void elsewhere_steps_aside_from_arrows_but_not_blades(GameTestHelper helper) {
        ServerPlayer player = TestPlayers.create(helper);
        try {
            setInt(player, "spawnInvulnerableTime", 0);
            player.moveTo(helper.absoluteVec(new Vec3(7.5, 1, 7.5)));
            player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(ModItems.SWORD.get(SchoolSteel.ENDER).get()));
            Husk archer = helper.spawn(EntityType.HUSK, new BlockPos(2, 1, 2));
            archer.setNoAi(true);
            Vec3 start = player.position();
            float health = player.getHealth();
            Arrow arrow = new Arrow(helper.getLevel(), archer);
            boolean hit = player.hurt(helper.getLevel().damageSources().arrow(arrow, archer), 6.0F);
            helper.assertTrue(!hit && player.getHealth() == health, "the arrow finds nobody there");
            helper.assertTrue(player.position().distanceTo(start) > 0.5, "the wielder is elsewhere, moved " + player.position().distanceTo(start));

            boolean cut = player.hurt(helper.getLevel().damageSources().mobAttack(archer), 4.0F);
            helper.assertTrue(cut && player.getHealth() < health, "melee is not dodged");
        } finally {
            TestPlayers.remove(player);
        }
        helper.succeed();
    }

    // ------------------------------------------------------------------------------------------ helpers

    private static void use(GameTestHelper helper, ServerPlayer player, BlockPos relative) {
        BlockPos pos = helper.absolutePos(relative);
        BlockHitResult hit = new BlockHitResult(Vec3.atCenterOf(pos), Direction.UP, pos, false);
        helper.getLevel().getBlockState(pos).use(helper.getLevel(), player, InteractionHand.MAIN_HAND, hit);
    }

    /** Casts an instant spell at a block, as a survival player with plenty of mana. */
    private static void cast(GameTestHelper helper, ServerPlayer player, String spellId, BlockPos target) {
        helper.assertTrue(startCast(helper, player, spellId, target), spellId + " cast starts");
    }

    private static boolean startCast(GameTestHelper helper, ServerPlayer player, String spellId, BlockPos target) {
        player.getAttribute(AttributeRegistry.MAX_MANA.get()).setBaseValue(10000);
        MagicData.getPlayerMagicData(player).setMana(10000);
        MagicData.getPlayerMagicData(player).getPlayerCooldowns().clearCooldowns();
        player.lookAt(EntityAnchorArgument.Anchor.EYES, Vec3.atCenterOf(helper.absolutePos(target)));
        AbstractSpell spell = SpellRegistry.getSpell(new ResourceLocation(spellId));
        helper.assertTrue(spell != SpellRegistry.none(), spellId + " is registered");
        return spell.attemptInitiateCast(ItemStack.EMPTY, spell.getMinLevel(), helper.getLevel(), player, CastSource.SPELLBOOK, true, "mainhand");
    }

    private static double sum(Collection<AttributeModifier> modifiers) {
        return modifiers.stream().mapToDouble(AttributeModifier::getAmount).sum();
    }

    private static boolean near(double a, double b) {
        return Math.abs(a - b) < 1e-6;
    }

    private static void setInt(Object target, String name, int value) {
        try {
            Class<?> type = target.getClass();
            while (type != null) {
                try {
                    Field field = type.getDeclaredField(name);
                    field.setAccessible(true);
                    field.setInt(target, value);
                    return;
                } catch (NoSuchFieldException next) {
                    type = type.getSuperclass();
                }
            }
            throw new NoSuchFieldException(name);
        } catch (ReflectiveOperationException failure) {
            throw new IllegalStateException("cannot set " + name + " on " + target, failure);
        }
    }
}
