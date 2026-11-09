package dev.dragonsteelschools.registry;

import dev.dragonsteelschools.DragonsteelSchools;
import dev.dragonsteelschools.item.DawnItem;
import dev.dragonsteelschools.item.ElsewhereItem;
import dev.dragonsteelschools.forge.FinishingRule;
import dev.dragonsteelschools.item.LoreItem;
import dev.dragonsteelschools.item.SchoolPlateArmorItem;
import dev.dragonsteelschools.item.SchoolStaffItem;
import dev.dragonsteelschools.item.SchoolSwordItem;
import dev.dragonsteelschools.item.SchoolTiers;
import dev.dragonsteelschools.school.SchoolSteel;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.AxeItem;
import net.minecraft.world.item.HoeItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.PickaxeItem;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.ShovelItem;
import net.minecraft.world.item.Tier;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;

/**
 * Per-school items. Weapon numbers reproduce Ice and Fire 2.1.13's dragonsteel attack modifiers on a vanilla tier
 * (attack bonus 21): sword +24, pickaxe +25, axe +29, shovel +25.5, hoe +1, so the tooltips read 25 / 26 / 30 /
 * 26.5 / 2 attack damage exactly as Ice and Fire's do.
 */
public final class ModItems {
    public static final DeferredRegister<Item> ITEMS = DeferredRegister.create(ForgeRegistries.ITEMS, DragonsteelSchools.MODID);

    public static final Map<SchoolSteel, RegistryObject<Item>> BLOOD = new EnumMap<>(SchoolSteel.class);
    public static final Map<SchoolSteel, RegistryObject<Item>> TEMPERED = new EnumMap<>(SchoolSteel.class);
    public static final Map<SchoolSteel, RegistryObject<Item>> INGOT = new EnumMap<>(SchoolSteel.class);
    public static final Map<SchoolSteel, RegistryObject<Item>> HELMET = new EnumMap<>(SchoolSteel.class);
    public static final Map<SchoolSteel, RegistryObject<Item>> CHESTPLATE = new EnumMap<>(SchoolSteel.class);
    public static final Map<SchoolSteel, RegistryObject<Item>> LEGGINGS = new EnumMap<>(SchoolSteel.class);
    public static final Map<SchoolSteel, RegistryObject<Item>> BOOTS = new EnumMap<>(SchoolSteel.class);
    public static final Map<SchoolSteel, RegistryObject<Item>> SWORD = new EnumMap<>(SchoolSteel.class);
    public static final Map<SchoolSteel, RegistryObject<Item>> PICKAXE = new EnumMap<>(SchoolSteel.class);
    public static final Map<SchoolSteel, RegistryObject<Item>> AXE = new EnumMap<>(SchoolSteel.class);
    public static final Map<SchoolSteel, RegistryObject<Item>> SHOVEL = new EnumMap<>(SchoolSteel.class);
    public static final Map<SchoolSteel, RegistryObject<Item>> HOE = new EnumMap<>(SchoolSteel.class);
    public static final Map<SchoolSteel, RegistryObject<Item>> STAFF = new EnumMap<>(SchoolSteel.class);

    /** Creative tab order. */
    public static final List<RegistryObject<Item>> ORDERED = new ArrayList<>();

    static {
        for (SchoolSteel school : SchoolSteel.values()) {
            String s = school.id();
            BLOOD.put(school, add(s + "_dragon_blood",
                    () -> new LoreItem(new Item.Properties().rarity(Rarity.UNCOMMON), "item.dragonsteel_schools.dragon_blood.lore", school)));
            TEMPERED.put(school, add("tempered_" + s + "_steel",
                    () -> new LoreItem(new Item.Properties().fireResistant().rarity(Rarity.UNCOMMON),
                            () -> "item.dragonsteel_schools.tempered_steel.lore." + FinishingRule.forTooltip().langSuffix(), school)));
            INGOT.put(school, add(s + "_dragonsteel_ingot",
                    () -> new LoreItem(new Item.Properties().fireResistant().rarity(Rarity.UNCOMMON), "item.dragonsteel_schools.dragonsteel_ingot.lore", school)));
            HELMET.put(school, add(s + "_dragonsteel_helmet", () -> new SchoolPlateArmorItem(school, ArmorItem.Type.HELMET, armorProps())));
            CHESTPLATE.put(school, add(s + "_dragonsteel_chestplate", () -> new SchoolPlateArmorItem(school, ArmorItem.Type.CHESTPLATE, armorProps())));
            LEGGINGS.put(school, add(s + "_dragonsteel_leggings", () -> new SchoolPlateArmorItem(school, ArmorItem.Type.LEGGINGS, armorProps())));
            BOOTS.put(school, add(s + "_dragonsteel_boots", () -> new SchoolPlateArmorItem(school, ArmorItem.Type.BOOTS, armorProps())));
            SWORD.put(school, add(school.swordId(), () -> switch (school) {
                case HOLY -> new DawnItem(SchoolTiers.of(school), 3, -2.4F, weaponProps());
                case ENDER -> new ElsewhereItem(SchoolTiers.of(school), 3, -2.4F, weaponProps());
                default -> new SchoolSwordItem(school, SchoolTiers.of(school), 3, -2.4F, weaponProps());
            }));
            PICKAXE.put(school, add(s + "_dragonsteel_pickaxe", () -> new PickaxeItem(tier(school), 4, -2.8F, toolProps())));
            AXE.put(school, add(s + "_dragonsteel_axe", () -> new AxeItem(tier(school), 8.0F, -3.0F, toolProps())));
            SHOVEL.put(school, add(s + "_dragonsteel_shovel", () -> new ShovelItem(tier(school), 4.5F, -3.0F, toolProps())));
            HOE.put(school, add(s + "_dragonsteel_hoe", () -> new HoeItem(tier(school), -20, -3.0F, toolProps())));
            STAFF.put(school, add(school.staffId(), () -> new SchoolStaffItem(school)));
        }
    }

    private ModItems() {
    }

    private static RegistryObject<Item> add(String name, java.util.function.Supplier<Item> factory) {
        RegistryObject<Item> item = ITEMS.register(name, factory);
        ORDERED.add(item);
        return item;
    }

    private static Tier tier(SchoolSteel school) {
        return SchoolTiers.of(school);
    }

    private static Item.Properties armorProps() {
        return new Item.Properties().fireResistant().stacksTo(1).rarity(Rarity.EPIC);
    }

    private static Item.Properties weaponProps() {
        return new Item.Properties().fireResistant().rarity(Rarity.EPIC);
    }

    private static Item.Properties toolProps() {
        return new Item.Properties().fireResistant().rarity(Rarity.RARE);
    }

    public static List<RegistryObject<Item>> armorPieces(SchoolSteel school) {
        return List.of(HELMET.get(school), CHESTPLATE.get(school), LEGGINGS.get(school), BOOTS.get(school));
    }
}
