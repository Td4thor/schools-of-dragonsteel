package dev.dragonsteelschools.compat.jei;

import dev.dragonsteelschools.DragonsteelSchools;
import dev.dragonsteelschools.combat.SwordPowers;
import dev.dragonsteelschools.config.DSConfig;
import dev.dragonsteelschools.forge.ApexForgingRecipe;
import dev.dragonsteelschools.forge.ForgeBatchMath;
import dev.dragonsteelschools.registry.ModItems;
import dev.dragonsteelschools.registry.ModRegistries;
import dev.dragonsteelschools.school.SchoolSteel;
import io.redspace.ironsspellbooks.api.registry.SpellRegistry;
import io.redspace.ironsspellbooks.api.spells.AbstractSpell;
import io.redspace.ironsspellbooks.api.spells.SpellRarity;
import mezz.jei.api.IModPlugin;
import mezz.jei.api.JeiPlugin;
import mezz.jei.api.helpers.IGuiHelper;
import mezz.jei.api.recipe.RecipeType;
import mezz.jei.api.registration.IRecipeCatalystRegistration;
import mezz.jei.api.registration.IRecipeCategoryRegistration;
import mezz.jei.api.registration.IRecipeRegistration;
import mezz.jei.api.runtime.IJeiRuntime;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientPacketListener;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/**
 * JEI pages that explain the mod: how school blood is brewed, which spells finish each school's tempered steel, and
 * an information page on every item (bloods, steels, ingots, swords, staves, armour). The breath-tempering and staff
 * recipes are Ice and Fire forge recipes, which Ice and Fire's own JEI plugin already shows.
 *
 * <p>JEI is optional: only JEI loads this class. Nothing here imports Ice and Fire; the forges come from the
 * {@code dragonsteel_schools:dragon_forge_cores} block tag.
 */
@JeiPlugin
public final class DragonsteelJeiPlugin implements IModPlugin {
    static final RecipeType<FinishingRecipe> FINISHING = RecipeType.create(DragonsteelSchools.MODID, "finishing", FinishingRecipe.class);
    static final RecipeType<BloodRecipe> BLOOD = RecipeType.create(DragonsteelSchools.MODID, "dragon_blood", BloodRecipe.class);
    private static final ResourceLocation UID = new ResourceLocation(DragonsteelSchools.MODID, "jei");
    private static final TagKey<Block> FORGE_CORES = TagKey.create(Registries.BLOCK, new ResourceLocation(DragonsteelSchools.MODID, "dragon_forge_cores"));
    private static volatile IJeiRuntime runtime;

    @Override
    public ResourceLocation getPluginUid() {
        return UID;
    }

    /** JEI's runtime once it is up (the dev client QA opens the pages through it). */
    @Nullable
    public static IJeiRuntime runtime() {
        return runtime;
    }

    public static RecipeType<FinishingRecipe> finishingType() {
        return FINISHING;
    }

    public static RecipeType<BloodRecipe> bloodType() {
        return BLOOD;
    }

    @Override
    public void registerCategories(IRecipeCategoryRegistration registration) {
        IGuiHelper gui = registration.getJeiHelpers().getGuiHelper();
        registration.addRecipeCategories(new BloodCategory(gui), new FinishingCategory(gui));
    }

    @Override
    public void registerRecipes(IRecipeRegistration registration) {
        registration.addRecipes(BLOOD, bloodRecipes());
        registration.addRecipes(FINISHING, finishingRecipes());
        information(registration);
    }

    @Override
    public void registerRecipeCatalysts(IRecipeCatalystRegistration registration) {
        registration.addRecipeCatalyst(new ItemStack(Items.CAULDRON), BLOOD);
        for (ItemStack forge : forgeCores()) {
            registration.addRecipeCatalyst(forge, FINISHING);
        }
    }

    @Override
    public void onRuntimeAvailable(IJeiRuntime jeiRuntime) {
        runtime = jeiRuntime;
    }

    @Override
    public void onRuntimeUnavailable() {
        runtime = null;
    }

    // ------------------------------------------------------------------------------------------------------------

    private static List<BloodRecipe> bloodRecipes() {
        List<BloodRecipe> out = new ArrayList<>();
        for (SchoolSteel school : SchoolSteel.values()) {
            out.add(new BloodRecipe(school, new ItemStack(ModItems.BLOOD.get(school).get()), spellsOf(school)));
        }
        return out;
    }

    /**
     * For each finishing recipe (data-driven, so datapacks are honoured): first the school's Apex spells, then every
     * spell of the school that reaches Legendary rarity, from the lowest level that does.
     */
    private static List<FinishingRecipe> finishingRecipes() {
        List<FinishingRecipe> out = new ArrayList<>();
        for (ApexForgingRecipe recipe : apexForgingRecipes()) {
            ItemStack[] inputs = recipe.input().getItems();
            if (inputs.length == 0) {
                continue;
            }
            ItemStack tempered = inputs[0].copy();
            ItemStack ingot = recipe.result().copy();
            SchoolSteel school = recipe.school();
            for (String id : DSConfig.get(DSConfig.APEX_SPELLS)) {
                AbstractSpell spell = SpellRegistry.getSpell(id);
                if (spell != null && spell != SpellRegistry.none() && SchoolSteel.bySchool(spell.getSchoolType().getId()).orElse(null) == school) {
                    out.add(new FinishingRecipe(school, tempered, ingot, spell, spell.getMinLevel(), true));
                }
            }
            List<FinishingRecipe> legendary = new ArrayList<>();
            for (AbstractSpell spell : spellsOf(school)) {
                if (DSConfig.isApex(spell.getSpellId()) || DSConfig.isLegendaryExcluded(spell.getSpellId())) {
                    continue;
                }
                int level = legendaryFrom(spell);
                if (level > 0) {
                    legendary.add(new FinishingRecipe(school, tempered, ingot, spell, level, false));
                }
            }
            legendary.sort(Comparator.comparingInt(FinishingRecipe::minLevel).thenComparing(r -> r.spell().getSpellId()));
            out.addAll(legendary);
        }
        return out;
    }

    /** The lowest level at which the spell is of Legendary rarity (as FinishingRule.finishes judges it), or 0. */
    private static int legendaryFrom(AbstractSpell spell) {
        for (int level = Math.max(1, spell.getMinLevel()); level <= spell.getMaxLevel(); level++) {
            if (spell.getRarity(level) == SpellRarity.LEGENDARY) {
                return level;
            }
        }
        return 0;
    }

    private static List<ApexForgingRecipe> apexForgingRecipes() {
        ClientPacketListener connection = Minecraft.getInstance().getConnection();
        if (connection != null) {
            List<ApexForgingRecipe> recipes = new ArrayList<>(connection.getRecipeManager().getAllRecipesFor(ModRegistries.APEX_FORGING.get()));
            recipes.sort(Comparator.comparingInt(r -> r.school().ordinal()));
            return recipes;
        }
        List<ApexForgingRecipe> fallback = new ArrayList<>();
        for (SchoolSteel school : SchoolSteel.values()) {
            fallback.add(new ApexForgingRecipe(new ResourceLocation(DragonsteelSchools.MODID, school.id() + "_dragonsteel_ingot"), school,
                    net.minecraft.world.item.crafting.Ingredient.of(ModItems.TEMPERED.get(school).get()), new ItemStack(ModItems.INGOT.get(school).get())));
        }
        return fallback;
    }

    /** The school's enabled spells, by spell id. */
    private static List<AbstractSpell> spellsOf(SchoolSteel school) {
        List<AbstractSpell> out = new ArrayList<>();
        for (AbstractSpell spell : SpellRegistry.REGISTRY.get().getValues()) {
            if (spell != SpellRegistry.none() && spell.isEnabled() && spell.getSchoolType() != null
                    && school.schoolId().equals(spell.getSchoolType().getId())) {
                out.add(spell);
            }
        }
        out.sort(Comparator.comparing(AbstractSpell::getSpellId));
        return out;
    }

    /** One stack of each core in the forge-core tag (Ice and Fire's fire, ice and lightning forges, when present). */
    private static List<ItemStack> forgeCores() {
        Set<Item> items = new LinkedHashSet<>();
        BuiltInRegistries.BLOCK.getTag(FORGE_CORES).ifPresent(tag -> tag.forEach(holder -> {
            Item item = holder.value().asItem();
            // a forge's core turns into its _disabled twin once built; only the plain core is an item players hold
            if (item != Items.AIR && !BuiltInRegistries.ITEM.getKey(item).getPath().endsWith("_disabled")) {
                items.add(item);
            }
        }));
        List<ItemStack> out = new ArrayList<>();
        items.forEach(item -> out.add(new ItemStack(item)));
        return out;
    }

    // ------------------------------------------------------------------------------------------------------------

    private static void information(IRecipeRegistration registration) {
        String cauldronRange = fmt(DSConfig.get(DSConfig.CAULDRON_RANGE));
        String finishingRange = fmt(DSConfig.get(DSConfig.FINISHING_RANGE));
        registration.addItemStackInfo(new ItemStack(Items.DRAGON_BREATH), info("dragon_breath"));
        for (SchoolSteel school : SchoolSteel.values()) {
            Component name = school.displayName();
            registration.addItemStackInfo(new ItemStack(ModItems.BLOOD.get(school).get()),
                    info("blood", name, cauldronRange), info("blood.uses", name));
            registration.addItemStackInfo(new ItemStack(ModItems.TEMPERED.get(school).get()),
                    info("tempered", name), info("tempered.finish", name, ForgeBatchMath.MAX_PER_CAST, finishingRange),
                    info("tempered.apex_only"));
            registration.addItemStackInfo(new ItemStack(ModItems.INGOT.get(school).get()),
                    info("ingot", name, Component.translatable(ModItems.SWORD.get(school).get().getDescriptionId())));
            registration.addItemStackInfo(new ItemStack(ModItems.STAFF.get(school).get()), info("staff", name));
            List<ItemStack> armour = new ArrayList<>();
            ModItems.armorPieces(school).forEach(piece -> armour.add(new ItemStack(piece.get())));
            registration.addItemStackInfo(armour, info("armor", fmt(DSConfig.get(DSConfig.ARMOR_MAX_MANA)),
                    fmt(DSConfig.get(DSConfig.ARMOR_SPELL_POWER) * 100.0), fmt(DSConfig.get(DSConfig.ARMOR_SCHOOL_POWER) * 100.0), name));
            List<ItemStack> tools = List.of(new ItemStack(ModItems.PICKAXE.get(school).get()), new ItemStack(ModItems.AXE.get(school).get()),
                    new ItemStack(ModItems.SHOVEL.get(school).get()), new ItemStack(ModItems.HOE.get(school).get()));
            registration.addItemStackInfo(tools, info("tools", name));
            registration.addItemStackInfo(new ItemStack(ModItems.SWORD.get(school).get()), swordInfo(school));
        }
    }

    private static Component[] swordInfo(SchoolSteel school) {
        return switch (school) {
            case HOLY -> new Component[]{info("dawn", fmt(DSConfig.get(DSConfig.DAWN_UNDEAD_BONUS)), DSConfig.get(DSConfig.DAWN_HOLY_FIRE_SECONDS),
                    fmt(DSConfig.get(DSConfig.HOLY_FIRE_DAMAGE)), fmt(DSConfig.get(DSConfig.HOLY_FIRE_UNDEAD_MULTIPLIER)))};
            case ENDER -> {
                List<Component> lines = new ArrayList<>();
                lines.add(info(DSConfig.get(DSConfig.ELSEWHERE_SPELL_PROJECTILES) ? "elsewhere" : "elsewhere.arrows", DSConfig.get(DSConfig.ELSEWHERE_RADIUS)));
                lines.add(info(DSConfig.get(DSConfig.ELSEWHERE_OFFHAND) ? "elsewhere.either_hand" : "elsewhere.main_hand"));
                double cooldown = DSConfig.get(DSConfig.ELSEWHERE_COOLDOWN_SECONDS);
                if (cooldown > 0.0) {
                    lines.add(info("elsewhere.cooldown", fmt(cooldown)));
                }
                yield lines.toArray(new Component[0]);
            }
            default -> new Component[]{Component.translatable("item.dragonsteel_schools." + school.swordId() + ".power", SwordPowers.tooltipArgs(school)),
                    info(school.swordId())};
        };
    }

    private static Component info(String key, Object... args) {
        return Component.translatable("jei.dragonsteel_schools.info." + key, args);
    }

    static String fmt(double value) {
        return value == Math.rint(value) ? Integer.toString((int) value) : String.format(Locale.ROOT, "%.1f", value);
    }
}
