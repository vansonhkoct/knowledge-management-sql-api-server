import unicodedata

def is_standard_char(char):
    try:
        name = unicodedata.name(char)
        print(char, name, ord(char))
        return ord(char) <= 127 or name.startswith("CJK") or name.startswith("LATIN") or name.startswith("GREEK") or name.startswith("CYRILLIC")
    except (ValueError, TypeError):
        return False

def contains_non_standard_chars(text):
    total_count = 0
    abnormal_count = 0
    for char in text:
        total_count += 1
        if not is_standard_char(char):
            abnormal_count += 1

    return abnormal_count / total_count



text = "Ѓ஠ĵㄴᗿᔔ஦ᆯጐĵㄴᗿᔔశਅዏĵ\n ĺ‒⥉ۨ৑঵ΡቂɢĻẇ\n## ᅖᏤপ։๲ѡᯆፂ ؏·ƾ㙊ΠۿᔔశЃ஠ĵƠ⟳ۨ৑፯ጐ"
print("abnormality: ", contains_non_standard_chars(text))

text = "英基學校特殊學校私立中學按位津貼學校#繁简转换说明：简体中文转繁体中文转简体中文进行互相翻译。 ᔔᓽဥ⇇や❎ݩ⡉⡁гᔔᓽဥ⇇や❎ݩ⡉⡁гᔔᓽဥ⇇や❎ݩ⡉⡁гᔔᓽဥ⇇や❎ݩ⡉⡁гᔔᓽဥ⇇や❎ݩ⡉⡁гᔔᓽဥ⇇や❎ݩ⡉⡁гᔔᓽဥ⇇や❎ݩ⡉⡁г\n ṵƾ⾀ᑇݪᴥ⢰᷋ṵƾ⾀ᑇݪᴥ⢰᷋ṵƾ⾀ᑇݪᴥ⢰᷋ṵƾ⾀ᑇݪᴥ⢰᷋ṵƾ⾀ᑇݪᴥ⢰᷋ṵƾ⾀ᑇݪᴥ⢰᷋ ๲ѡၥሑ๲ѡၥሑ๲ѡၥሑ\n## ໠⢰ႁ\n## ᯆፂ\n#### ⥜ဥ୒⯝Ɓᐕ໣༤ᐓᳯᮆᔔᓽ\n ஁ᄽႁ\n ᱮ⤶㘼ѵ๵ၧ஁ᄽ⯎⯮\n ஁ᄽႁ\n ᮆĺ‒⥉ۨ৑঵ΡቂɢĻ фఃဥ୒чтᵄᄺ௟ṃ⊑⠓ਇ ⢰᷋ᄸషƁʫ໠⢰ႁ਄ᄺ⊧✞む໠⤩ᄳ͖௪ ⴌᔔЃĵႠᔔ঴ᔔᮆ⇸т\n## ⢰᷋঵໩\n#### ؏·Ɓ㙊⢚⤶ᔔᓽݪᅖΠᖧĵㄴᗿᔔశ"
print("abnormality: ", contains_non_standard_chars(text))


def remove_non_standard_chars(text):
    """
    Remove non-standard characters from the given text.
    """
    cleaned_text = ""
    for char in text:
        try:
            # Get the Unicode name of the character
            name = unicodedata.name(char)
            # Check if the character is a standard Latin, Greek, or Cyrillic character
            if ord(char) <= 127 or name.startswith("CHINESE") or name.startswith("LATIN") or name.startswith("GREEK") or name.startswith("CYRILLIC"):
                cleaned_text += char
        except (ValueError, TypeError):
            # If the character is not a recognized Unicode character, skip it
            pass
    return cleaned_text

text = "英基學校# ᔔᓽဥ⇇や❎ݩ⡉⡁гᔔᓽဥ⇇や❎ݩ⡉⡁гᔔᓽဥ⇇や❎ݩ⡉⡁гᔔᓽဥ⇇や❎ݩ⡉⡁гᔔᓽဥ⇇や❎ݩ⡉⡁гᔔᓽဥ⇇や❎ݩ⡉⡁гᔔᓽဥ⇇や❎ݩ⡉⡁г\n ṵƾ⾀ᑇݪᴥ⢰᷋ṵƾ⾀ᑇݪᴥ⢰᷋ṵƾ⾀ᑇݪᴥ⢰᷋ṵƾ⾀ᑇݪᴥ⢰᷋ṵƾ⾀ᑇݪᴥ⢰᷋ṵƾ⾀ᑇݪᴥ⢰᷋ ๲ѡၥሑ๲ѡၥሑ๲ѡၥሑ\n## ໠⢰ႁ\n## ᯆፂ\n#### ⥜ဥ୒⯝Ɓᐕ໣༤ᐓᳯᮆᔔᓽ\n ஁ᄽႁ\n ᱮ⤶㘼ѵ๵ၧ஁ᄽ⯎⯮\n ஁ᄽႁ\n ᮆĺ‒⥉ۨ৑঵ΡቂɢĻ фఃဥ୒чтᵄᄺ௟ṃ⊑⠓ਇ ⢰᷋ᄸషƁʫ໠⢰ႁ਄ᄺ⊧✞む໠⤩ᄳ͖௪ ⴌᔔЃĵႠᔔ঴ᔔᮆ⇸т\n## ⢰᷋঵໩\n#### ؏·Ɓ㙊⢚⤶ᔔᓽݪᅖΠᖧĵㄴᗿᔔశ"
print("clearned: ", remove_non_standard_chars(text))
print("clearned: ", contains_non_standard_chars(remove_non_standard_chars(text)))
