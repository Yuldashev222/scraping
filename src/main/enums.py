from enum import Enum
from django.db.models import TextChoices

exact_words = ['juster']


class FileMode(TextChoices):
    KOMMUN = 'k', "Kommun"
    REGION = 'r', "Region"


class Organ(TextChoices):
    S = "s", "kommunstyrelsen"
    F = "f", "kommunfullmäktige"
    HALSO = 'halso', "Hälso- och sjukvårdsnämnden"
    KOLLEK = 'kollek', "Kollektivtrafiknämnden"
    REGLA = 'regla', "Regionala utvecklingsnämnden"


class InformCountry(Enum):
    nor = 'Norrbotten'
    ble = 'Blekinge'
    dal = 'Dalarna'
    got = 'Gotland'
    gav = 'Gävleborg'
    hal = 'Halland'
    jam = 'Jämtland'
    jon = 'Jönköping'
    kal = 'Kalmar'
    kro = 'Kronoberg'
    ska = 'Skåne'
    sto = 'Stockholm'
    sod = 'Södermanland'
    upp = 'Uppsala'
    var = 'Värmland'
    vab = 'Västerbotten'
    van = 'Västernorrland'
    vam = 'Västmanland'
    vag = 'Västra Götaland'
    ore = 'Örebro'
    ost = 'Östergötland'

    @classmethod
    def choices(cls):
        result = [(_.name, _.value) for _ in cls]
        result.sort(key=lambda x: x[1])
        return result

    @classmethod
    def values(cls):
        result = [_.value.lower() for _ in cls]
        result.sort()
        return result

    @classmethod
    def keys(cls):
        result = [_.name for _ in cls]
        return result


class InformRegion(Enum):
    nor_arj = 'Arjeplog'
    nor_arv = 'Arvidsjaur'
    nor_bod = 'Boden'
    nor_gal = 'Gällivare'
    nor_hap = 'Haparanda'
    nor_jok = 'Jokkmokk'
    nor_kal = 'Kalix'
    nor_kir = 'Kiruna'
    nor_lul = 'Luleå'
    nor_paj = 'Pajala'
    nor_pit = 'Piteå'
    nor_alv = 'Älvsbyn'
    nor_kve = 'Överkalix'
    nor_tve = 'Övertorneå'

    ble_har = 'Karlshamn'
    ble_rar = 'Karlskrona'
    ble_olo = 'Olofström'
    ble_ron = 'Ronneby'
    ble_sol = 'Sölvesborg'

    dal_ave = 'Avesta'
    dal_bor = 'Borlänge'
    dal_fal = 'Falun'
    dal_gag = 'Gagnef'
    dal_hed = 'Hedemora'
    dal_lek = 'Leksand'
    dal_lud = 'Ludvika'
    dal_mal = 'Malung-Sälen'
    dal_mor = 'Mora'
    dal_ors = 'Orsa'
    dal_rat = 'Rättvik'
    dal_sme = 'Smedjebacken'
    dal_sat = 'Säter'
    dal_van = 'Vansbro'
    dal_alv = 'Älvdalen'

    got_got = 'Gotland'

    gav_bol = 'Bollnäs'
    gav_gav = 'Gävle'
    gav_hof = 'Hofors'
    gav_hud = 'Hudiksvall'
    gav_lju = 'Ljusdal'
    gav_nor = 'Nordanstig'
    gav_ock = 'Ockelbo'
    gav_ova = 'Ovanåker'
    gav_san = 'Sandviken'
    gav_sod = 'Söderhamn'

    hal_fal = 'Falkenberg'
    hal_hal = 'Halmstad'
    hal_hyl = 'Hylte'
    hal_kun = 'Kungsbacka'
    hal_var = 'Varberg'
    hal_lah = 'Laholm'

    jam_ber = 'Berg'
    jam_bra = 'Bräcke'
    jam_har = 'Härjedalen'
    jam_kro = 'Krokom'
    jam_rag = 'Ragunda'
    jam_str = 'Strömsund'
    jam_are = 'Åre'
    jam_ost = 'Östersund'

    jon_ane = 'Aneby'
    jon_eks = 'Eksjö'
    jon_gis = 'Gislaved'
    jon_gno = 'Gnosjö'
    jon_hab = 'Habo'
    jon_jon = 'Jönköping'
    jon_mul = 'Mullsjö'
    jon_nas = 'Nässjö'
    jon_sav = 'Sävsjö'
    jon_tra = 'Tranås'
    jon_vag = 'Vaggeryd'
    jon_vet = 'Vetlanda'
    jon_var = 'Värnamo'

    kal_bor = 'Borgholm'
    kal_emm = 'Emmaboda'
    kal_hul = 'Hultsfred'
    kal_hog = 'Högsby'
    kal_kal = 'Kalmar'
    kal_mon = 'Mönsterås'
    kal_mor = 'Mörbylånga'
    kal_nyb = 'Nybro'
    kal_osk = 'Oskarshamn'
    kal_tor = 'Torsås'
    kal_vim = 'Vimmerby'
    kal_vas = 'Västervik'

    kro_alv = 'Alvesta'
    kro_les = 'Lessebo'
    kro_lju = 'Ljungby'
    kro_mar = 'Markaryd'
    kro_tin = 'Tingsryd'
    kro_upp = 'Uppvidinge'
    kro_vax = 'Växjö'
    kro_alm = 'Älmhult'

    ska_bju = 'Bjuv'
    ska_bro = 'Bromölla'
    ska_bur = 'Burlöv'
    ska_bas = 'Båstad'
    ska_esl = 'Eslöv'
    ska_hel = 'Helsingborg'
    ska_has = 'Hässleholm'
    ska_hog = 'Höganäs'
    ska_hor = 'Hörby'
    ska_hoo = 'Höör'
    ska_kli = 'Klippan'
    ska_kri = 'Kristianstad'
    ska_kav = 'Kävlinge'
    ska_lan = 'Landskrona'
    ska_lom = 'Lomma'
    ska_lun = 'Lund'
    ska_mal = 'Malmö'
    ska_osb = 'Osby'
    ska_per = 'Perstorp'
    ska_sim = 'Simrishamn'
    ska_sjo = 'Sjöbo'
    ska_sku = 'Skurup'
    ska_sta = 'Staffanstorp'
    ska_sva = 'Svalöv'
    ska_sve = 'Svedala'
    ska_tom = 'Tomelilla'
    ska_tre = 'Trelleborg'
    ska_vel = 'Vellinge'
    ska_yst = 'Ystad'
    ska_ast = 'Åstorp'
    ska_ost = 'Östra Göinge'
    ska_ang = 'Ängelholm'
    ska_ork = 'Örkelljunga'

    sto_bot = 'Botkyrka'
    sto_dan = 'Danderyd'
    sto_eke = 'Ekerö'
    sto_han = 'Haninge'
    sto_hud = 'Huddinge'
    sto_jar = 'Järfälla'
    sto_lid = 'Lidingö'
    sto_nac = 'Nacka'
    sto_nor = 'Norrtälje'
    sto_nyk = 'Nykvarn'
    sto_nyn = 'Nynäshamn'
    sto_sal = 'Salem'
    sto_sig = 'Sigtuna'
    sto_sol = 'Sollentuna'
    sto_son = 'Solna'
    sto_sto = 'Stockholm'
    sto_sun = 'Sundbyberg'
    sto_sod = 'Södertälje'
    sto_tyr = 'Tyresö'
    sto_tab = 'Täby'
    sto_upp = 'Upplands Väsby'
    sto_upb = 'Upplands-Bro'
    sto_val = 'Vallentuna'
    sto_vax = 'Vaxholm'
    sto_var = 'Värmdö'
    sto_ost = 'Österåker'

    sod_esk = 'Eskilstuna'
    sod_fle = 'Flen'
    sod_gne = 'Gnesta'
    sod_kat = 'Katrineholm'
    sod_nyk = 'Nyköping'
    sod_oxe = 'Oxelösund'
    sod_str = 'Strängnäs'
    sod_tro = 'Trosa'
    sod_vin = 'Vingåker'

    upp_enk = 'Enköping'
    upp_heb = 'Heby'
    upp_hab = 'Håbo'
    upp_kni = 'Knivsta'
    upp_tie = 'Tierp'
    upp_upp = 'Uppsala'
    upp_alv = 'Älvkarleby'
    upp_ost = 'Östhammar'

    var_arv = 'Arvika'
    var_eda = 'Eda'
    var_fil = 'Filipstad'
    var_for = 'Forshaga'
    var_gru = 'Grums'
    var_hag = 'Hagfors'
    var_ham = 'Hammarö'
    var_kar = 'Karlstad'
    var_kil = 'Kil'
    var_kri = 'Kristinehamn'
    var_mun = 'Munkfors'
    var_sto = 'Storfors'
    var_sun = 'Sunne'
    var_saf = 'Säffle'
    var_tor = 'Torsby'
    var_arj = 'Årjäng'

    vab_bju = 'Bjurholm'
    vab_dor = 'Dorotea'
    vab_lyc = 'Lycksele'
    vab_mal = 'Malå'
    vab_nor = 'Nordmaling'
    vab_nos = 'Norsjö'
    vab_rob = 'Robertsfors'
    vab_ske = 'Skellefteå'
    vab_sor = 'Sorsele'
    vab_sto = 'Storuman'
    vab_ume = 'Umeå'
    vab_vil = 'Vilhelmina'
    vab_vin = 'Vindeln'
    vab_van = 'Vännäs'
    vab_ase = 'Åsele'

    van_har = 'Härnösand'
    van_kra = 'Kramfors'
    van_sol = 'Sollefteå'
    van_sun = 'Sundsvall'
    van_tim = 'Timrå'
    van_ang = 'Ånge'
    van_orn = 'Örnsköldsvik'

    vam_arb = 'Arboga'
    vam_fag = 'Fagersta'
    vam_hal = 'Hallstahammar'
    vam_kun = 'Kungsör'
    vam_kop = 'Köping'
    vam_nor = 'Norberg'
    vam_sal = 'Sala'
    vam_ski = 'Skinnskatteberg'
    vam_sur = 'Surahammar'
    vam_vas = 'Västerås'

    vag_ale = 'Ale'
    vag_ali = 'Alingsås'
    vag_ben = 'Bengtsfors'
    vag_bol = 'Bollebygd'
    vag_bor = 'Borås'
    vag_dal = 'Dals-Ed'
    vag_ess = 'Essunga'
    vag_fal = 'Falköping'
    vag_far = 'Färgelanda'
    vag_gra = 'Grästorp'
    vag_gul = 'Gullspång'
    vag_got = 'Göteborg'
    vag_goe = 'Götene'
    vag_her = 'Herrljunga'
    vag_hjo = 'Hjo'
    vag_har = 'Härryda'
    vag_kar = 'Karlsborg'
    vag_kun = 'Kungälv'
    vag_ler = 'Lerum'
    vag_lid = 'Lidköping'
    vag_lil = 'Lilla Edet'
    vag_lys = 'Lysekil'
    vag_mar = 'Mariestad'
    vag_mak = 'Mark'
    vag_mel = 'Mellerud'
    vag_mun = 'Munkedal'
    vag_mol = 'Mölndal'
    vag_oru = 'Orust'
    vag_par = 'Partille'
    vag_ska = 'Skara'
    vag_sko = 'Skövde'
    vag_sot = 'Sotenäs'
    vag_ste = 'Stenungsund'
    vag_str = 'Strömstad'
    vag_sve = 'Svenljunga'
    vag_tan = 'Tanum'
    vag_tib = 'Tibro'
    vag_tid = 'Tidaholm'
    vag_tjo = 'Tjörn'
    vag_tra = 'Tranemo'
    vag_tro = 'Trollhättan'
    vag_tor = 'Töreboda'
    vag_udd = 'Uddevalla'
    vag_ulr = 'Ulricehamn'
    vag_var = 'Vara'
    vag_vag = 'Vårgårda'
    vag_van = 'Vänersborg'
    vag_ama = 'Åmål'
    vag_ock = 'Öckerö'

    ore_ask = 'Askersund'
    ore_deg = 'Degerfors'
    ore_hal = 'Hallsberg'
    ore_hae = 'Hällefors'
    ore_kar = 'Karlskoga'
    ore_kum = 'Kumla'
    ore_lax = 'Laxå'
    ore_lek = 'Lekeberg'
    ore_lin = 'Lindesberg'
    ore_nor = 'Nora'
    ore_ore = 'Örebro'
    ore_lju = 'Ljusnarsberg'

    ost_box = 'Boxholm'
    ost_fin = 'Finspång'
    ost_kin = 'Kinda'
    ost_lin = 'Linköping'
    ost_mjo = 'Mjölby'
    ost_mot = 'Motala'
    ost_nor = 'Norrköping'
    ost_sod = 'Söderköping'
    ost_vad = 'Vadstena'
    ost_val = 'Valdemarsvik'
    ost_ydr = 'Ydre'
    ost_atv = 'Åtvidaberg'
    ost_ode = 'Ödeshög'

    @classmethod
    def choices(cls):
        result = [(_.name, _.value) for _ in cls]
        result.sort(key=lambda x: x[1])
        return result

    @classmethod
    def values(cls):
        result = [_.value.lower() for _ in cls]
        result.sort()
        return result

    @classmethod
    def keys(cls):
        result = [_.name for _ in cls]
        return result
