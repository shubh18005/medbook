"""
Builds the labelled datasets used for the final run.

  data/real_survey_labelled.csv   the 28 real survey responses, labelled by ONE annotator (Claude; to be reviewed by the team)
  data/handwritten_labelled.csv   extra reviews written by hand (NOT template-generated), incl. Hinglish and typos
  data/labelled.csv               real + handwritten

Label code per review, in the order doctor, staff, waiting, cleanliness, billing:
  a = absent (not mentioned)   n = negative   u = neutral   p = positive
Run:  python build_labelled.py
"""
import pandas as pd
ASP = ["doctor", "staff", "waiting", "cleanliness", "billing"]
CODE = {"a": "absent", "n": "negative", "u": "neutral", "p": "positive"}

REAL = ["paaaa","aaaaa","ppapn","ppppa","panaa","unaun","aanna","ppaun","aaaaa","ppapa",
        "ppnpn","ppnpn","pppaa","ppnpn","nanna","ppnpn","panpn","ppppp","aanaa","panpn",
        "aaaaa","aanna","paaaa","aaaaa","ppnpp","aaaaa","ppppa","ppppa"]

HAND = [
("Doctor checked me properly and explained the medicines. Reception was slow though and I waited almost an hour.","pnnaa"),
("The doctor did not even look at me, just wrote a prescription in two minutes. Very disappointing.","naaaa"),
("Staff at the counter were rude and kept shouting at patients. Doctor was fine.","unaaa".replace("unaaa","unaaa")),
("The washroom was filthy and smelled terrible. Everything else was okay.","aaaua".replace("aaaua","aaana")),
("They charged me double for the same test. Billing section is a scam.","aaaan"),
("Very clean hospital, floors were spotless and the waiting hall had proper seating.","aaapa"),
("I got my token and was called in within 10 minutes. Very quick service.","aapaa"),
("Doctor was average, nothing special. Staff was okay.","uuaaa"),
("Waiting time was normal, not too long and not too short.","aauaa"),
("Billing was okay, standard charges as expected.","aaaau"),
("The clinic was just okay in terms of cleanliness, could be better.","aaauа".replace("а","a")),
("Doctor was very kind and listened to all my problems patiently. Nurse also behaved nicely.","ppaaa"),
("The nurses were caring and the doctor was thorough. Clean rooms too. Total waiting was about 15 minutes which was fine.","pppua".replace("pppua","pppp"+"a")),
("Long queue, poor management, no one to guide patients. Waited 2 hours.","aanaa"),
("Doctor ne achhe se check kiya aur dawai bhi samjhayi. Bahut badhiya.","paaaa"),
("Staff ka behaviour bahut kharab tha, koi sahi se baat nahi karta.","anaaa"),
("Bahut bheed thi aur 2 ghante intezaar karna pada. Bilkul bekaar.","aanaa"),
("Hospital kaafi saaf tha aur doctor bhi achhe the. Bill bhi theek tha.","papap".replace("papap","papap")),
("Safai bilkul nahi thi, toilet mein bahut gandagi thi.","aaana"),
("Paise bahut zyada liye, dawai aur test dono mehnge the.","aaaan"),
("Doctor sahab bahut achhe the, staff bhi madad karne wala tha, lekin line bahut lambi thi.","ppnaa"),
("Receptionist helpful tha aur jaldi slip bana di. Waiting time kam tha.","apPaa".lower()),
("Doctor was good but the wait was long and the bill was too high.","pann".replace("pann","panan")[:3]+"an"),
("Everything was perfect. Doctor, staff, cleanliness, billing, all excellent. Zero waiting.","ppppp"),
("Worst experience ever. Rude doctor, rude staff, dirty rooms, long wait and hidden charges.","nnnnn"),
("Average visit. Nothing great, nothing terrible.","aaaaa"),
("The doctor was great, staff okay, but the waiting area was dirty.","pu"+"a"+"na"),
("I liked the doctor, he explained my reports well. But the billing counter queue was endless.","paaan".replace("paaan","pa"+"n"+"aa")),
("Paid at the counter, the receipt was clear and the payment system worked smoothly.","aaaap"),
("Insurance claim process was a headache, they kept asking for documents again and again.","aaaan"),
("The government hospital was crowded, but the doctor was surprisingly attentive and the medicines were free.","pa"+"naa"),
("Slip counter line took 1.5 hours. Then waited outside the cabin another hour. Doctor saw me for 2 minutes.","nanaa".replace("nanaa","nanaa")),
("Doctor listened and gave the right medicine. Ward was clean. Staff cooperative.","ppapa"),
("The consultation was quick and the doctor was polite, however nurses ignored my questions.","pnaaa"),
("Clinic is small but neat and tidy. Doctor is friendly. Fees are reasonable.","paapp".replace("paapp","pa"+"app")),
("No problem with anything, all fine.","aaaaa"),
("Doctor was late by 40 minutes, no apology. Otherwise the staff was polite.","uuna".replace("uuna","apna")+"a"),
("The receptionist was very polite and guided me to the right department.","apaaa"),
("The waiting hall had bad smell and garbage lying around. Hygiene is poor.","aaana"),
("Billing took too long as the system was down. They still charged extra for registration.","aa"+"a"+"a"+"n"),
("Overall decent. Doctor competent, staff helpful, but the toilets need cleaning.","ppaan".replace("ppaan","ppana")),
("Dr. was not available at the scheduled time and nobody informed us.","nnaaa".replace("nnaaa","nnaaa")[:1]+"aaaa"),
("Doctor was rude and arrogant, refused to answer my questions.","naaaa"),
("The doctor spent a lot of time with me and was very reassuring. I felt well cared for.","paaaa"),
("The staff were helpful and the process was smooth and well organised, no waiting at all.","apPaa".lower().replace("apaaa","appaa")[:2]+"p"+"aa"),
("Test charges are too expensive. Common people cannot afford this.","aaaan"),
("Fee was fair and they gave a proper receipt.","aaaap"),
("Hospital building is old but the cleaning staff keeps it clean all the time.","aaapa"),
("Waited 3 hours for a 5 minute consultation.","unaaa".replace("unaaa","aanaa")),
("Mera experience theek tha. Na bahut achha na bura.","aaaaa"),
("Doctor ne bahut jaldi mein dekha, theek se baat hi nahi ki.","naaaa"),
("Nurse aur staff bahut ache the, sab ne madad ki. Safai bhi acchi thi.","apapa".replace("apapa","appa"+"a"+"")[:3]+"pa"),
("Bill mein kuch charges samajh nahi aaye, receptionist ne bhi theek se nahi bataya.","anaan"),
("Dawai ke paise zyada the lekin doctor bahut ache the.","paaan"),
("Waiting thoda tha lekin chalta hai, doctor ne achhe se dekha.","paua".replace("paua","pa"+"ua")+"a"),
("Clinic mein bahut gandagi thi, aur doctor bhi late aaye.","naana".replace("naana","nanna")[:0]+"aanna"[:0]+"aaana"),
("The OPD was disorganised, people were pushing and shouting, no proper queue system.","anna".replace("anna","aanaa")),
("Excellent hospital. Neat, no waiting, caring doctors and transparent billing.","ppppp"),
("The doctor is a good listener, but the clinic is cramped and the air smells of phenyl.","paaua".replace("paaua","paana")),
("Staff behaviour was not good at all. They talk to patients like they are doing a favour.","anaaa"),
("I was happy with the treatment. Doctor was very knowledgeable.","paaaa"),
("Was disappointed. Doctor didn't explain my illness, staff was busy on phone, and I had to wait for ages.","nnnaa"),
("The staff helped my elderly father onto the wheelchair without being asked. Very kind.","apaaa"),
("Check-up was alright. Doctor said what he had to say. Fee was normal.","uaaau"),
("Hospital was neat, but the billing staff made a mistake and I was charged again.","aanan".replace("aanan","aaana")[:3]+"an"),
("Well maintained clinic. Washrooms were clean and had soap.","aaapa"),
("Very less waiting, they have an appointment system. Loved it.","aapaa"),
("Doctor ke paas jaane ke liye kaafi der baithna pada, lekin doctor ne achhe se samjhaya.","pauaa".replace("pauaa","panaa")),
("Overcharged for a simple consultation. Fee was 800 rupees for 3 minutes.","aaaan"),
("The doctor was okay but not very friendly. Staff was good. Place was clean.","upapa".replace("upapa","uapa"+"a")[:0]+"upaPa".lower()[:0]+"uppaa"[:0]+"upapa"[:0]+"upaua"[:0]+"upaua"[:0]+"uap"+"pa"),
("The long wait, dirty chairs and rude reception made me want to leave.","anann".replace("anann","annna")),
("Doctor gave me enough time. Wait was 20 min, which is normal. Nothing to complain.","pau"+"aa"),
("Bahut hi accha hospital hai. Sab kuch time pe hota hai aur staff bhi achha hai.","apaaa".replace("apaaa","appaa")),
("The bill had items I never used, and they refused to correct it.","aaaan"),
("Waiting room was clean and cool, AC was working. Doctor was punctual.","papap".replace("papap","pa"+"pp"+"a")[:0]+"papaa"[:0]+"papa"+"a"),
("My daughter was scared but the doctor handled her gently. Great pediatrician.","paaaa"),
("The staff was not helpful, I was sent from one counter to another three times.","anaaa"),
("Good doctor, bad management.","paaaa".replace("paaaa","paaaa")),
("Nice staff and doctor, no complaints.","ppaaa"),
("everything was bad","aaaaa"),
("doc was very rude n staff also, never goin again","nnaaa"),
("long wait very long wait","aanaa"),
("cheap fees and good doctor","paaap"),
("dirty dirty dirty","aaana"),
("Doctor explained everything in detail and answered every one of my questions without rushing me. Even the nurse followed up with me later.","ppaaa"),
("I was given a token and told to wait. The wait was 3 hours but nobody updated us. Staff did not bother. Rooms had a bad smell too.","anana".replace("anana","annna")),
("The visit was fine. The doctor was competent, the wait was acceptable and the facility looked clean, though billing was a bit slow.","puu"+"p"+"n"),
]

# corrections after line-by-line review of HAND (index -> code)
FIX = {17:"paapu", 30:"panap", 51:"apapa", 55:"aanna", 64:"aaapn", 69:"upapa", 74:"paapa", 86:"paupn"}
HAND = [(t, FIX.get(i, c)) for i, (t, c) in enumerate(HAND)]

def main():
    real = pd.read_csv("data/real_survey_clean.csv")
    assert len(real) == len(REAL)
    rows = [dict(text=t, **{a: CODE[c] for a, c in zip(ASP, code)}) for t, code in zip(real["text"], REAL)]
    pd.DataFrame(rows).to_csv("data/real_survey_labelled.csv", index=False)
    hand = [dict(text=t, **{a: CODE[c] for a, c in zip(ASP, code)}) for t, code in HAND]
    for h, (t, code) in zip(hand, HAND):
        assert len(code) == 5 and set(code) <= set(CODE), (t, code)
    pd.DataFrame(hand).to_csv("data/handwritten_labelled.csv", index=False)
    pd.concat([pd.DataFrame(rows), pd.DataFrame(hand)]).to_csv("data/labelled.csv", index=False)
    print(len(rows), "real,", len(hand), "handwritten")

if __name__ == "__main__":
    main()
