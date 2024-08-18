import unicodedata

def is_standard_char(char):
    try:
        if ord(char) <= 127:
          return True

        name = unicodedata.name(char)
        is_valid = (
          False
          or name.startswith("CJK") 
          or name.startswith("FULLWIDTH") 
          or name.startswith("IDEOGRAPHIC") 
          or not (
            False
            or name.startswith("CYRILLIC")
            or name.startswith("LATIN")
            or name.startswith("CIRCLED LATIN")
            or name.startswith("HANGUL")
            or name.startswith("CANADIAN")
            or name.startswith("ETHIOPIC")
            or name.startswith("TELUGU")
            or name.startswith("GURMUKHI")
            or name.startswith("ARABIC")
            or name.startswith("GREEK")
            or name.startswith("CHEROKEE")
            or name.startswith("BENGALI")
            or name.startswith("ARMENIAN")
            or name.startswith("BATAK")
            or name.startswith("ARABIC")
            or name.startswith("MALAYALAM")
          )
          # or (name.startswith("LATIN") 
          # or name.startswith("GREEK") 
          # or name.startswith("CYRILLIC")
        )
        print(is_valid, char, name, ord(char))
        return is_valid
    except (ValueError, TypeError) as e:
        print(ord(char))
        print(f"Exception {e}")
        return False

def contains_non_standard_chars(text):
    total_count = 0
    abnormal_count = 0
    for char in text:
        total_count += 1
        if not is_standard_char(char):
            abnormal_count += 1

    print(f"{abnormal_count}/{total_count}")
    return abnormal_count / total_count



text = "Ѓ஠ĵㄴᗿᔔ஦ᆯጐĵㄴᗿᔔశਅዏĵ\n ĺ‒⥉ۨ৑঵ΡቂɢĻẇ\n## ᅖᏤপ։๲ѡᯆፂ ؏·ƾ㙊ΠۿᔔశЃ஠ĵƠ⟳ۨ৑፯ጐ"
print("abnormality: ", contains_non_standard_chars(text))

# text = "檔號：EDB/CDI/MCNE3/ADM/50/1/1(1)\n\n教育局通函第 161/2023 號\n\n\n分發名單： 各中、小學及特殊學校校長\n\n（英基學校協會屬下學校及國\n\n際學校除外）\n\n\n副本送：各組主管—備考\n\n\n## 「2024 年國家安全齊參與」計劃\n\n本通函旨在邀請學校參加由教育局和保安局合辦的「2024 年國家安全齊參\n\n\n摘要\n\n\n與」計劃。\n\n教育局和保安局合辦「國家安全齊參與」計劃，得到學校鼎力支持和鼓勵\n\n學生積極參與。為繼續加強師生維護國家安全的意識和責任感，並培育青少年\n\n成為愛國愛港的新一代，以及為香港踏入由治及興的新征程注入力量，教育局\n\n和保安局在 2023/24 學年繼續合辦「2024 年國家安全齊參與」計劃，讓全港師\n\n生共同參與，深化師生對《憲法》、《基本法》及國家安全的認識，加強自覺\n\n維護國家安全的意識，讓國家安全教育植根校園。\n\n「2024 年國家安全齊參與」計劃設三項活動，讓師生參與。學校可鼓勵\n\n及安排師生參與下列一項或多於一項活動，包括：\n\ni). 「2024 國家安全寫作比賽」（附錄一）\n\nii). 「2024 國家安全校園壁報設計比賽」（附錄二）\n\niii). 「2024 國家安全教案設計優秀作品選」（附錄三）\n\n4. 為便利學校推動國家安全教育，教育局持續透過「國民教育\n\n一站通」網上資源平台 [(www.edb.gov.hk/tc/neosp)](http://www.edb.gov.hk/tc/neosp) 及「國家安全教\n\n育資源網頁」 [(www.edb.gov.hk/nser)](http://www.edb.gov.hk/nser) ，發放與《憲法》、《基本\n\n法》及國家安全教育相關的多元化資源，加強學生的國民身份認\n\n同，以及深化他們維護國家安全的意識和責任感。學校亦可鼓勵師\n\n\n-----"
# print("abnormality: ", contains_non_standard_chars(text))

# text = "檔號：EDB/CDI/MCNE3/ADM/50/1/1(1)\n\n教育局通函第 161/2023 號\n\n\n分發名單： 各中、小學及特殊學校校長\n\n（英基學校協會屬下學校及國\n\n際學校除外）\n\n\n副本送：各組主管—備考\n\n\n## 「2024 年國家安全齊參與」計劃\n\n本通函旨在邀請學校參加由教育局和保安局合辦的「2024 年國家安全齊參\n\n\n摘要\n\n\n與」計劃。\n\n教育局和保安局合辦「國家安全齊參與」計劃，得到學校鼎力支持和鼓勵\n\n學生積極參與。為繼續加強師生維護國家安全的意識和責任感，並培育青少年\n\n成為愛國愛港的新一代，以及為香港踏入由治及興的新征程注入力量，教育局\n\n和保安局在 2023/24 學年繼續合辦「2024 年國家安全齊參與」計劃，讓全港師\n\n生共同參與，深化師生對《憲法》、《基本法》及國家安全的認識，加強自覺\n\n維護國家安全的意識，讓國家安全教育植根校園。\n\n「2024 年國家安全齊參與」計劃設三項活動，讓師生參與。學校可鼓勵\n\n及安排師生參與下列一項或多於一項活動，包括：\n\ni). 「2024 國家安全寫作比賽」（附錄一）\n\nii). 「2024 國家安全校園壁報設計比賽」（附錄二）\n\niii). 「2024 國家安全教案設計優秀作品選」（附錄三）\n\n4. 為便利學校推動國家安全教育，教育局持續透過「國民教育\n\n一站通」網上資源平台 [(www.edb.gov.hk/tc/neosp)](http://www.edb.gov.hk/tc/neosp) 及「國家安全教\n\n育資源網頁」 [(www.edb.gov.hk/nser)](http://www.edb.gov.hk/nser) ，發放與《憲法》、《基本\n\n法》及國家安全教育相關的多元化資源，加強學生的國民身份認\n\n同，以及深化他們維護國家安全的意識和責任感。學校亦可鼓勵師\n\n\n-----"
# print("abnormality: ", contains_non_standard_chars(text))

# text = """
# 112233445566778899 Saturn V rocket’s first stage carries 203,400 gallons (770,000 liters) of kerosene fuel and 318,000 gallons (1.2 million liters) of liquid oxygen needed for combustion. At liftoff, the stage’s five F-1 rocket engines ignite and produce 7.5 million pounds of thrust.
# //// 1111 ^^^^ 2222 — — 3333 !!!! 4444 &&&& 5555 %%%% 6666 ???? 7777
# To replace those goofy quantities with the far less retarded metric system (even though liters are considered part of the metric system they are the same as cubic deci-meters) you would say 770 cubic meters of kerosene {abbreviated as m3} and 1,204 m3 of liquid O2 [O2 is the symbol for oxygen]. We would also say it produced 33,600,000 newtons of force <abbreviated as N>.
# — — 3333 ~~~~ 9999 :::: 8888 ;;;; 6776 ```` 2332 ‘’’’ 3323 “””” 4343 @@@@
# """
# print("abnormality: ", contains_non_standard_chars(text))

# text = """
# <<<< >>>> {{{{ }}}} (((( )))) [[[[ ]]]]
# Another way to write scientific notation is to replace the “* 10 ^” with ‘E’ -/capital e\-. So our numbers would look like:s
# #### 7.7 E 2
# ==== 1.2 E 3
# %%%% 3.3 E 7
# ???? %%%% &&&& !!!! ^^^^ — — **** ++++ ====
# """
# print("abnormality: ", contains_non_standard_chars(text))

# text = """
# To add scientific notation {a way of writing numbers that allows you to write only as many digits `of specificity` as you would like} you can write 7.7 * 10 ^ 2 m3 of kerosene 1.204 * 10 ^ 3 m3 of O2 and 3.3 * 10 ^ 7 newtons.
# """
# print("abnormality: ", contains_non_standard_chars(text))

# text = """
# 💥😾  ⓐşＤ𝕗𝔞Ş∂ℱⒹⓈⓐ𝔽ⓓ𝓢άgÃｄѕⒻ∂Ａⓢ𝔽ⓢ𝐀𝐃𝐒ᗪ𝓪
# Ƒ
# ⓐ𝔻𝓢ғ
# ｓＡｄ
# Ŧⓐⓢ
# ᗪ  ♩ൠ

# 😎♖  Δｓ𝓭𝒻ａ𝔰๔ᖴⒹⓢ𝓐Ｆ๔şᵃⒼ𝔸ĐŜ𝒇𝐝𝓐Ｓᶠs𝔸ⓓⓈ𝐝ค
# Ƒ
# 𝕒𝕕ｓ𝒻
# ⓢ𝒶∂
# ᖴＡ丂
# ∂  😾🌷

# ★·.·´¯`·.·★   🎀  𝒶𝓈𝒹𝒻𝒶𝓈𝒹𝒻𝒹𝓈𝒶𝒻𝒹𝓈𝒶𝑔𝒶𝒹𝓈𝒻𝒹𝒶𝓈𝒻𝓈𝒶𝒹𝓈𝒹𝒶
# 𝒻
# 𝒶𝒹𝓈𝒻
# 𝓈𝒶𝒹
# 𝒻𝒶𝓈
# 𝒹  🎀   ★·.·`¯´·.·★

# 🍓  🎀  𝒶𝓈𝒹𝒻𝒶𝓈𝒹𝒻𝒹𝓈𝒶𝒻𝒹𝓈𝒶𝑔𝒶𝒹𝓈𝒻𝒹𝒶𝓈𝒻𝓈𝒶𝒹𝓈𝒹𝒶
# 𝒻
# 𝒶𝒹𝓈𝒻
# 𝓈𝒶𝒹
# 𝒻𝒶𝓈
# 𝒹  🎀  🍓

# 🍰 ⋆ 🍫  🎀  𝒶𝓈𝒹𝒻𝒶𝓈𝒹𝒻𝒹𝓈𝒶𝒻𝒹𝓈𝒶𝑔𝒶𝒹𝓈𝒻𝒹𝒶𝓈𝒻𝓈𝒶𝒹𝓈𝒹𝒶
# 𝒻
# 𝒶𝒹𝓈𝒻
# 𝓈𝒶𝒹
# 𝒻𝒶𝓈
# 𝒹  🎀  🍫 ⋆ 🍰
# """
# print("abnormality: ", contains_non_standard_chars(text))

text = """
中學展板圖樣


-----
"""
print("abnormality: ", contains_non_standard_chars(text))





# def remove_non_standard_chars(text):
#     """
#     Remove non-standard characters from the given text.
#     """
#     cleaned_text = ""
#     for char in text:
#         try:
#             # Get the Unicode name of the character
#             name = unicodedata.name(char)
#             # Check if the character is a standard Latin, Greek, or Cyrillic character
#             if ord(char) <= 127 or name.startswith("CHINESE") or name.startswith("LATIN") or name.startswith("GREEK") or name.startswith("CYRILLIC"):
#                 cleaned_text += char
#         except (ValueError, TypeError):
#             # If the character is not a recognized Unicode character, skip it
#             pass
#     return cleaned_text

# text = "英基學校# ᔔᓽဥ⇇や❎ݩ⡉⡁гᔔᓽဥ⇇や❎ݩ⡉⡁гᔔᓽဥ⇇や❎ݩ⡉⡁гᔔᓽဥ⇇や❎ݩ⡉⡁гᔔᓽဥ⇇や❎ݩ⡉⡁гᔔᓽဥ⇇や❎ݩ⡉⡁гᔔᓽဥ⇇や❎ݩ⡉⡁г\n ṵƾ⾀ᑇݪᴥ⢰᷋ṵƾ⾀ᑇݪᴥ⢰᷋ṵƾ⾀ᑇݪᴥ⢰᷋ṵƾ⾀ᑇݪᴥ⢰᷋ṵƾ⾀ᑇݪᴥ⢰᷋ṵƾ⾀ᑇݪᴥ⢰᷋ ๲ѡၥሑ๲ѡၥሑ๲ѡၥሑ\n## ໠⢰ႁ\n## ᯆፂ\n#### ⥜ဥ୒⯝Ɓᐕ໣༤ᐓᳯᮆᔔᓽ\n ஁ᄽႁ\n ᱮ⤶㘼ѵ๵ၧ஁ᄽ⯎⯮\n ஁ᄽႁ\n ᮆĺ‒⥉ۨ৑঵ΡቂɢĻ фఃဥ୒чтᵄᄺ௟ṃ⊑⠓ਇ ⢰᷋ᄸషƁʫ໠⢰ႁ਄ᄺ⊧✞む໠⤩ᄳ͖௪ ⴌᔔЃĵႠᔔ঴ᔔᮆ⇸т\n## ⢰᷋঵໩\n#### ؏·Ɓ㙊⢚⤶ᔔᓽݪᅖΠᖧĵㄴᗿᔔశ"
# print("clearned: ", remove_non_standard_chars(text))
# print("clearned: ", contains_non_standard_chars(remove_non_standard_chars(text)))
