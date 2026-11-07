package dev.dragonsteelschools.gametest;

import dev.dragonsteelschools.DragonsteelSchools;
import dev.dragonsteelschools.registry.ModBlocks;
import dev.dragonsteelschools.registry.ModItems;
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
import net.minecraft.gametest.framework.GameTestSequence;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Container;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.animal.Pig;
import net.minecraft.world.entity.monster.Husk;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LayeredCauldronBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

import java.lang.reflect.Field;
import java.util.List;

/** Blood, Evocation, Nature and Eldritch: their blood, their Apex forging and their swords' powers. */
@GameTestHolder(DragonsteelSchools.MODID)
@PrefixGameTestTemplate(false)
public final class SchoolGameTests {
    /** One Iron's spell per new school, cast at the cauldron. Eldritch must be learned first. */
    private static final List<SchoolSteel> NEW = List.of(SchoolSteel.BLOOD, SchoolSteel.EVOCATION, SchoolSteel.NATURE, SchoolSteel.ELDRITCH);
    private static final List<String> CAULDRON_SPELLS = List.of("irons_spellbooks:heartstop", "irons_spellbooks:shield",
            "irons_spellbooks:oakskin", "irons_spellbooks:abyssal_shroud");

    private SchoolGameTests() {
    }

    // ------------------------------------------------------------------------------------------ cauldron

    @GameTest(template = "platform", timeoutTicks = 400)
    public static void cauldron_each_new_school_brews_its_own_blood(GameTestHelper helper) {
        ServerPlayer player = TestPlayers.create(helper);
        player.moveTo(helper.absoluteVec(new Vec3(7.5, 2, 2.5)));
        GameTestSequence seq = helper.startSequence();
        for (int i = 0; i < NEW.size(); i++) {
            SchoolSteel school = NEW.get(i);
            String spell = CAULDRON_SPELLS.get(i);
            BlockPos pos = new BlockPos(3 + 3 * i, 2, 9);
            seq.thenExecuteAfter(i == 0 ? 1 : 40, () -> {
                helper.setBlock(pos.below(), Blocks.STONE);
                helper.setBlock(pos, ModBlocks.BREATH_CAULDRON.get().defaultBlockState().setValue(LayeredCauldronBlock.LEVEL, 3));
                cast(helper, player, spell, pos);
            }).thenExecuteAfter(30, () -> {
                BlockState state = helper.getBlockState(pos);
                helper.assertTrue(state.is(ModBlocks.BLOOD_CAULDRON.get(school).get()) && state.getValue(LayeredCauldronBlock.LEVEL) == 3,
                        spell + " makes " + school + " blood, was " + state);
            });
        }
        seq.thenExecute(() -> TestPlayers.remove(player)).thenSucceed();
    }

    // ------------------------------------------------------------------------------------------ apex (one batch each)

    @GameTest(template = "platform", timeoutTicks = 700, batch = "apex_blood")
    public static void forge_blood_apex_finishes_blood_dragonsteel(GameTestHelper helper) {
        apex(helper, SchoolSteel.BLOOD, "grandsigil:crimson_threads", "grandsigil:colosseum");
    }

    @GameTest(template = "platform", timeoutTicks = 700, batch = "apex_evocation")
    public static void forge_evocation_apex_finishes_evocation_dragonsteel(GameTestHelper helper) {
        apex(helper, SchoolSteel.EVOCATION, "grandsigil:grand_sigil", "grandsigil:thousand_blades");
    }

    @GameTest(template = "platform", timeoutTicks = 700, batch = "apex_nature")
    public static void forge_nature_apex_finishes_nature_dragonsteel(GameTestHelper helper) {
        apex(helper, SchoolSteel.NATURE, "grandsigil:full_bloom", "grandsigil:world_tree");
    }

    @GameTest(template = "platform", timeoutTicks = 700, batch = "apex_eldritch")
    public static void forge_eldritch_apex_finishes_eldritch_dragonsteel(GameTestHelper helper) {
        apex(helper, SchoolSteel.ELDRITCH, "grandsigil:the_gaze", "grandsigil:black_coffin");
    }

    /** Tempered steel of the school in the output slot; the first of the school's Apex spells that will start. */
    private static void apex(GameTestHelper helper, SchoolSteel school, String... spells) {
        ApexCleanup.clear(helper);
        BlockPos core = new BlockPos(7, 3, 9);
        ForgeFixtures.build(helper, core, "fire", Direction.NORTH);
        ServerPlayer player = TestPlayers.create(helper);
        StringBuilder started = new StringBuilder();
        helper.runAfterDelay(5, () -> {
            Container forge = (Container) helper.getBlockEntity(core);
            forge.setItem(2, new ItemStack(ModItems.TEMPERED.get(school).get(), 10));
            forge.setItem(0, new ItemStack(ModItems.TEMPERED.get(SchoolSteel.HOLY).get(), 3));   // another school: untouched
            player.moveTo(helper.absoluteVec(new Vec3(7.5, 3, 2.5)));
            for (String spell : spells) {
                if (startCast(helper, player, spell, core)) {
                    started.append(spell);
                    break;
                }
            }
            helper.assertTrue(started.length() > 0, "one of " + String.join(", ", spells) + " starts");
        });
        helper.succeedWhen(() -> {
            Container forge = (Container) helper.getBlockEntity(core);
            ItemStack out = forge.getItem(2);
            helper.assertTrue(out.is(ModItems.INGOT.get(school).get()) && out.getCount() == 10,
                    started + " finishes 10 tempered " + school + " steel, output " + out);
            helper.assertTrue(forge.getItem(0).is(ModItems.TEMPERED.get(SchoolSteel.HOLY).get()) && forge.getItem(0).getCount() == 3,
                    "Holy steel left alone, input " + forge.getItem(0));
            TestPlayers.remove(player);
            ApexCleanup.clear(helper);
        });
    }

    // ------------------------------------------------------------------------------------------ swords

    @GameTest(template = "platform", timeoutTicks = 40)
    public static void thirst_heals_a_fifth_of_what_its_hits_take_and_nothing_from_spells(GameTestHelper helper) {
        ServerPlayer player = TestPlayers.create(helper);
        try {
            player.moveTo(helper.absoluteVec(new Vec3(7.5, 1, 6.5)));
            player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(ModItems.SWORD.get(SchoolSteel.BLOOD).get()));
            Zombie zombie = helper.spawn(EntityType.ZOMBIE, new BlockPos(7, 1, 8));
            zombie.setNoAi(true);
            zombie.getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.MAX_HEALTH).setBaseValue(200);
            zombie.setHealth(200);

            player.setHealth(4.0F);
            float before = zombie.getHealth();
            zombie.hurt(helper.getLevel().damageSources().playerAttack(player), 12.0F);
            float taken = before - zombie.getHealth();
            float healed = player.getHealth() - 4.0F;
            helper.assertTrue(taken > 0 && Math.abs(healed - taken * 0.2F) < 0.01F,
                    "a Thirst hit heals a fifth of the health it took: took " + taken + ", healed " + healed);

            player.setHealth(4.0F);
            zombie.invulnerableTime = 0;
            zombie.hurt(helper.getLevel().damageSources().indirectMagic(player, player), 12.0F);
            helper.assertTrue(player.getHealth() == 4.0F, "spell damage does not feed Thirst, health " + player.getHealth());

            player.setHealth(4.0F);
            zombie.invulnerableTime = 0;
            zombie.setHealth(1.0F);
            zombie.hurt(helper.getLevel().damageSources().playerAttack(player), 12.0F);
            float overkill = player.getHealth() - 4.0F;
            helper.assertTrue(Math.abs(overkill - 0.2F) < 0.01F, "overkill doesn't count: 1 health taken heals 0.2, healed " + overkill);
        } finally {
            TestPlayers.remove(player);
        }
        helper.succeed();
    }

    @GameTest(template = "platform", timeoutTicks = 40)
    public static void covenant_charged_hit_calls_fangs_then_waits_out_its_cooldown(GameTestHelper helper) {
        ServerPlayer player = TestPlayers.create(helper);
        player.moveTo(helper.absoluteVec(new Vec3(7.5, 1, 2.5)));
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(ModItems.SWORD.get(SchoolSteel.EVOCATION).get()));
        Pig pig = helper.spawn(EntityType.PIG, new BlockPos(7, 1, 5));
        pig.setNoAi(true);
        pig.getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.MAX_HEALTH).setBaseValue(500);
        pig.setHealth(500);
        player.lookAt(EntityAnchorArgument.Anchor.EYES, pig.getEyePosition());

        setInt(player, "attackStrengthTicker", 1000);
        player.attack(pig);
        int volley = helper.getLevel().getEntities(EntityType.EVOKER_FANGS, pig.getBoundingBox().inflate(16), e -> true).size();
        helper.assertTrue(volley == 6, "a charged hit calls 6 fangs, saw " + volley);

        pig.invulnerableTime = 0;
        setInt(player, "attackStrengthTicker", 1000);
        player.attack(pig);
        int after = helper.getLevel().getEntities(EntityType.EVOKER_FANGS, pig.getBoundingBox().inflate(16), e -> true).size();
        helper.assertTrue(after == volley, "a second charged hit inside the cooldown calls none, saw " + after);

        float before = pig.getHealth();
        helper.runAfterDelay(25, () -> {
            TestPlayers.remove(player);
            helper.assertTrue(pig.getHealth() < before, "the fangs bite, pig health " + before + " -> " + pig.getHealth());
            helper.succeed();
        });
    }

    @GameTest(template = "platform", timeoutTicks = 40)
    public static void briar_hits_poison_and_slow(GameTestHelper helper) {
        ServerPlayer player = TestPlayers.create(helper);
        try {
            player.moveTo(helper.absoluteVec(new Vec3(7.5, 1, 5.5)));
            player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(ModItems.SWORD.get(SchoolSteel.NATURE).get()));
            Pig pig = helper.spawn(EntityType.PIG, new BlockPos(7, 1, 7));
            pig.setNoAi(true);
            pig.getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.MAX_HEALTH).setBaseValue(500);
            pig.setHealth(500);
            player.attack(pig);
            helper.assertTrue(pig.hasEffect(MobEffects.POISON), "a Briar hit poisons");
            var slow = pig.getEffect(MobEffects.MOVEMENT_SLOWDOWN);
            helper.assertTrue(slow != null && slow.getAmplifier() == 1, "a Briar hit gives Slowness II, was " + slow);
        } finally {
            TestPlayers.remove(player);
        }
        helper.succeed();
    }

    @GameTest(template = "platform", timeoutTicks = 40)
    public static void hush_adds_four_damage_past_armour_and_darkens_players(GameTestHelper helper) {
        ServerPlayer wielder = TestPlayers.create(helper);
        ServerPlayer victim = TestPlayers.create(helper);
        try {
            wielder.moveTo(helper.absoluteVec(new Vec3(7.5, 1, 4.5)));
            Husk plain = armoured(helper, new BlockPos(4, 1, 8));
            Husk hushed = armoured(helper, new BlockPos(10, 1, 8));
            wielder.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.IRON_SWORD));
            float a = plain.getHealth();
            plain.hurt(helper.getLevel().damageSources().playerAttack(wielder), 10.0F);
            float plainTaken = a - plain.getHealth();
            wielder.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(ModItems.SWORD.get(SchoolSteel.ELDRITCH).get()));
            float b = hushed.getHealth();
            hushed.hurt(helper.getLevel().damageSources().playerAttack(wielder), 10.0F);
            float hushTaken = b - hushed.getHealth();
            helper.assertTrue(Math.abs(hushTaken - plainTaken - 4.0F) < 0.01F,
                    "Hush adds exactly 4 past netherite: plain " + plainTaken + ", hushed " + hushTaken);

            setInt(victim, "spawnInvulnerableTime", 0);
            victim.moveTo(helper.absoluteVec(new Vec3(7.5, 1, 6.0)));
            boolean pvp = helper.getLevel().getServer().isPvpAllowed();
            helper.getLevel().getServer().setPvpAllowed(true);   // the GameTest server starts with PvP off
            wielder.attack(victim);
            helper.getLevel().getServer().setPvpAllowed(pvp);
            helper.assertTrue(victim.hasEffect(MobEffects.DARKNESS), "a player struck by Hush is wrapped in Darkness");
        } finally {
            TestPlayers.remove(wielder);
            TestPlayers.remove(victim);
        }
        helper.succeed();
    }

    // ------------------------------------------------------------------------------------------ helpers

    private static Husk armoured(GameTestHelper helper, BlockPos pos) {
        Husk husk = helper.spawn(EntityType.HUSK, pos);
        husk.setNoAi(true);
        husk.getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.MAX_HEALTH).setBaseValue(200);
        husk.setHealth(200);
        husk.setItemSlot(EquipmentSlot.HEAD, new ItemStack(Items.NETHERITE_HELMET));
        husk.setItemSlot(EquipmentSlot.CHEST, new ItemStack(Items.NETHERITE_CHESTPLATE));
        husk.setItemSlot(EquipmentSlot.LEGS, new ItemStack(Items.NETHERITE_LEGGINGS));
        husk.setItemSlot(EquipmentSlot.FEET, new ItemStack(Items.NETHERITE_BOOTS));
        return husk;
    }

    private static void cast(GameTestHelper helper, ServerPlayer player, String spellId, BlockPos target) {
        helper.assertTrue(startCast(helper, player, spellId, target), spellId + " cast starts");
    }

    /** Starts a cast at a block as a survival player with plenty of mana; learns the spell first if it must be learned. */
    private static boolean startCast(GameTestHelper helper, ServerPlayer player, String spellId, BlockPos target) {
        player.getAttribute(AttributeRegistry.MAX_MANA.get()).setBaseValue(10000);
        MagicData magic = MagicData.getPlayerMagicData(player);
        magic.setMana(10000);
        magic.getPlayerCooldowns().clearCooldowns();
        player.lookAt(EntityAnchorArgument.Anchor.EYES, Vec3.atCenterOf(helper.absolutePos(target)));
        AbstractSpell spell = SpellRegistry.getSpell(new ResourceLocation(spellId));
        helper.assertTrue(spell != SpellRegistry.none(), spellId + " is registered");
        if (spell.requiresLearning()) {
            magic.getSyncedData().learnSpell(spell);
        }
        return spell.attemptInitiateCast(ItemStack.EMPTY, spell.getMinLevel(), helper.getLevel(), player, CastSource.SPELLBOOK, true, "mainhand");
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
            throw new IllegalArgumentException(name);
        } catch (IllegalAccessException failure) {
            throw new IllegalStateException(failure);
        }
    }
}
