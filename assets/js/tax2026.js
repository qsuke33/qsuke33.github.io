/*
 * 2026年（令和8年）分の給与所得者向け 税・社会保険料の概算ロジック。
 * 計算ツールのページ（/tools/）で共通に使う。数字を直すときはここだけ直す。
 *
 * 前提・出典（2026年11月時点）
 *  - 所得税：令和8年度税制改正（基礎控除 最大104万円、給与所得控除の最低保障74万円＝本則69万円＋令和8・9年分の特例5万円）
 *  - 住民税：基礎控除43万円。給与所得控除の最低保障は本則69万円で概算
 *  - 社会保険（令和8年度・本人負担）：協会けんぽ平均 健康保険9.90%の半分、介護1.62%の半分（40〜64歳）、
 *    子ども・子育て支援金0.23%の半分、厚生年金18.3%の半分、雇用保険（一般の事業）0.50%
 */
(function (global) {
  var RATES = {
    kenpo: 0.0990 / 2,
    kaigo: 0.0162 / 2,
    kosodate: 0.0023 / 2,
    kosei: 0.183 / 2,
    koyo: 0.0050,
    koseiMonthlyCap: 650000,   // 厚生年金 標準報酬月額の上限
    koseiBonusCap: 1500000,    // 厚生年金 標準賞与額の上限（1回）
    kenpoMonthlyCap: 1390000,  // 健康保険 標準報酬月額の上限
    kenpoBonusCapYear: 5730000 // 健康保険 標準賞与額の上限（年度累計）
  };

  function kyuyoKojo(s, minimum) {
    var k;
    if (s <= 1900000) k = 650000;
    else if (s <= 3600000) k = s * 0.3 + 80000;
    else if (s <= 6600000) k = s * 0.2 + 440000;
    else if (s <= 8500000) k = s * 0.1 + 1100000;
    else k = 1950000;
    return Math.min(s, Math.max(k, minimum));
  }
  function kisoShotoku(g) {
    if (g <= 4890000) return 1040000;
    if (g <= 6550000) return 670000;
    if (g <= 23500000) return 620000;
    if (g <= 24000000) return 480000;
    if (g <= 24500000) return 320000;
    if (g <= 25000000) return 160000;
    return 0;
  }
  function kisoJumin(g) {
    if (g <= 24000000) return 430000;
    if (g <= 24500000) return 290000;
    if (g <= 25000000) return 150000;
    return 0;
  }
  // 配偶者控除 [所得税, 住民税, 調整控除の人的控除差]
  function haigusha(g) {
    if (g <= 9000000) return [380000, 330000, 50000];
    if (g <= 9500000) return [260000, 220000, 40000];
    if (g <= 10000000) return [130000, 110000, 20000];
    return [0, 0, 0];
  }
  var BRACKETS = [
    [1950000, 0.05, 0], [3300000, 0.10, 97500], [6950000, 0.20, 427500],
    [9000000, 0.23, 636000], [18000000, 0.33, 1536000], [40000000, 0.40, 2796000],
    [Infinity, 0.45, 4796000]
  ];
  function bracket(t) {
    for (var i = 0; i < BRACKETS.length; i++) if (t <= BRACKETS[i][0]) return BRACKETS[i];
  }

  // 社会保険料（本人負担・年額）。月給はならして計算し、賞与は年2回同額として扱う。
  function socialInsurance(o) {
    var monthly = o.monthly, bonus = o.bonus || 0, half = bonus / 2;
    var kenpoRate = RATES.kenpo + RATES.kosodate + (o.age40to64 ? RATES.kaigo : 0);
    var kenpoBase = Math.min(monthly, RATES.kenpoMonthlyCap) * 12 + Math.min(bonus, RATES.kenpoBonusCapYear);
    var koseiBase = Math.min(monthly, RATES.koseiMonthlyCap) * 12 + Math.min(half, RATES.koseiBonusCap) * 2;
    var kenpo = kenpoBase * kenpoRate;
    var kosei = koseiBase * RATES.kosei;
    var koyo = (monthly * 12 + bonus) * RATES.koyo;
    return { kenpo: kenpo, kosei: kosei, koyo: koyo, total: kenpo + kosei + koyo };
  }

  /*
   * o: { salary, shaho, other, spouse(bool), dg, ds, dol, dot }
   *   dg: 一般扶養 ds: 特定扶養(19〜22歳) dol: 同居老親等 dot: その他の老人扶養
   *   extra: 給与以外の所得（副業の雑所得・事業所得など。売上−経費の額）
   */
  function taxes(o) {
    var salary = o.salary, shaho = o.shaho, other = o.other || 0;
    var dg = o.dg || 0, ds = o.ds || 0, dol = o.dol || 0, dot = o.dot || 0;
    var extra = o.extra || 0;
    var gT = Math.max(0, salary - kyuyoKojo(salary, 740000)) + extra;
    var gJ = Math.max(0, salary - kyuyoKojo(salary, 690000)) + extra;
    var sp = o.spouse ? haigusha(gJ) : [0, 0, 0];
    var depT = dg * 380000 + ds * 630000 + dol * 580000 + dot * 480000;
    var depJ = dg * 330000 + ds * 450000 + dol * 450000 + dot * 380000;
    var taxableT = Math.floor(Math.max(0, gT - shaho - other - kisoShotoku(gT) - sp[0] - depT) / 1000) * 1000;
    var taxableJ = Math.floor(Math.max(0, gJ - shaho - other - kisoJumin(gJ) - sp[1] - depJ) / 1000) * 1000;

    var diff = (gJ <= 25000000 ? 50000 : 0) + sp[2] + dg * 50000 + ds * 180000 + dol * 130000 + dot * 100000;
    var adj = 0;
    if (gJ <= 25000000 && taxableJ > 0) {
      adj = taxableJ <= 2000000 ? Math.min(diff, taxableJ) * 0.05
        : Math.max((diff - (taxableJ - 2000000)) * 0.05, 2500);
    }
    var shotokuwari = Math.max(0, taxableJ * 0.1 - adj);
    var kinto = (shotokuwari > 0 || gJ > 450000) ? 5000 : 0; // 均等割＋森林環境税（非課税ラインは概算）

    var b = taxableT > 0 ? bracket(taxableT) : [0, 0, 0];
    var incomeTax = Math.floor(Math.max(0, taxableT * b[1] - b[2]) * 1.021 / 100) * 100;

    return {
      gIncomeTax: gT, gJumin: gJ, taxableT: taxableT, taxableJ: taxableJ,
      rate: b[1], incomeTax: incomeTax, shotokuwari: shotokuwari,
      juminTax: Math.floor(shotokuwari / 100) * 100 + kinto
    };
  }

  function furusatoLimit(t) {
    if (t.shotokuwari <= 0) return 0;
    return t.shotokuwari * 0.2 / (0.9 - t.rate * 1.021) + 2000;
  }

  global.Tax2026 = {
    RATES: RATES, kyuyoKojo: kyuyoKojo, socialInsurance: socialInsurance,
    taxes: taxes, furusatoLimit: furusatoLimit
  };
})(window);
