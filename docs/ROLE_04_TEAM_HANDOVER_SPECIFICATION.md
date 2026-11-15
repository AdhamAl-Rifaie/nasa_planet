# RAG, LLM & Deterministic Conclusion Engine: Complete Team Integration Specification

> **NASA Space Apps 2026 — Trend Detective: What the Average Hides**  
> **Authoritative Role-by-Role Handover & API Data Contract Guide**  
> **Prepared by:** Role 04 (RAG & Conclusion Lead — Ahmed Lotfi)  
> **Verification Status:** 170/170 Unit, Adversarial & E2E Tests Passing (`pytest`)  
> **Primary Package:** `packages/rag/` (Single Service Surface: `packages/rag/facade.py`)

---

## 💡 القاعدة الذهبية للمشروع (Core Architectural Separation)

نظامنا يفصل بشكل صارم ومحكم بين مسارين لا يختلطان أبداً:
1. **مسار الأسئلة والمفاهيم العلمية (Concept Q&A Path):**  
   يعتمد على محرك بحث دلالي محلي (Bilingual BM25) على 469 مقطعاً موثقاً من ناسا، مع إمكانية استخدام LLM (`gemini-2.5-flash`) تحت حراسة بوابة تحقق برمجية صارمة جداً (Zero-Trust Output Validator). هذا المسار يشرح الوثائق ولا يولد أو يعدل أي أرقام حسابية.
2. **مسار الاستنتاجات الإحصائية التفاعلية (Statistical Conclusion Path):**  
   يعتمد بنسبة 100% على قوالب نصية حتمية مبرمجة في الكود (**Zero-LLM Deterministic Templates**) لضمان عدم تأليف أو هلوسة أو تغيير أي رقم إحصائي يخرج من محرك التحليل الخاص بـ Role 02.

---

## 1. كيف يعمل محرك Role 04 داخلياً (Five Verified Architectural Layers)

تم بناء حزمة `packages/rag/` وتوحيدها عبر واجهة واحدة `Role04Service` في `packages/rag/facade.py` كنظام **Offline-First ثنائي اللغة (عربي وإنجليزي)** مكون من 5 طبقات هندسية تم اختبارها بنسبة نجاح 100%:

```
[User / Frontend]
       │
       ▼
[Role04Service (packages/rag/facade.py)]
       ├── Path 1: Concept Q&A ──────────► [Bilingual BM25 (469 Chunks)]
       │                                            │
       │                                     (Optional Gemini)
       │                                            │
       │                                     [Zero-Trust Validator] ──► Verified Prose + Citations
       │
       └── Path 2: Statistical Conclusions ─► [normalize_result_payload()]
                                                    │
                                             [ActiveRequestTracker] (Anti-Stale Guard)
                                                    │
                                             [conclusions.py (Zero-LLM)] ──► Interactive Bilingual Segments + UI Actions
```

### تفاصيل الطبقات المعمارية الخمس:
1. **Phase 1: Provenance & Registry Readiness (`source_index.py`, `semantic_corpus.py`, `id_mapping.py`)**
   - 469 مقطعاً دلالياً مبنياً على الفقرات من 15 مصدراً رسمياً لناسا والأساليب الإحصائية، موثقة ببصمات SHA-256.
   - ربط ديناميكي بين المعرفات القديمة (`T2M`, `SoilMoi0_10cm_inst`, `GPM_3IMERGM`, `MOD13C2`, `ndvi`) والمعرفات المعمارية القياسية (`air_temperature`, `soil_moisture`, `precipitation`, `vegetation_greenness`).
   - عزل تام لعينة محطة القاهرة النقطية (`cairo_temperature_monthly.csv` بالسيليزيوس) عن شبكة MERRA-2 الشبكية المقاسة بالكلفن.
2. **Phase 2: Bilingual Retrieval & Semantic Guardrails (`arabic.py`, `aliases.py`, `intent.py`, `retriever.py`)**
   - تطبيع متقدم للغة العربية (إزالة التشكيل، توحيد الألف والتاء المربوطة، فصل علامات الترقيم `؟` و `،` و `؛`، توحيد الأرقام المشرقية `٠-٩` والغربية `0-9`، وفصل السوابق `وال`, `بال`, `لل`).
   - حواجز دلالية ذكية: كلمة `شتاء` تعتبر فصلاً ولا تربط تلقائياً بالأمطار؛ وكلمة `رطوبة` مجردة تطلب توضيحاً هل المقصود رطوبة تربة أم رطوبة جوية؛ والأسئلة الخارجة أو ذات دقة الشوارع/الأحياء تعود برفض مهذب وصريح.
3. **Phase 3: Gemini Client & Zero-Trust Output Validator (`provider.py`, `validator.py`, `explanation.py`)**
   - استدعاء `gemini-2.5-flash` بمهلة قصوى 8 ثوانٍ، وتمرير المفتاح في هيدر `x-goog-api-key` فقط (حجب المفتاح ومنع ظهوره في أي لوج أو كراش).
   - صمام أمان صارم: رفض أي حقول إضافية غير مصرح بها، التأكد من أن المقاطع المستشهد بها هي فقط من نتائج البحث الحالي، مطابقة أرقام الإصدارات، ومنع ادعاء السببية الزائفة، ومنع خلط الوحدات.
   - التحول التلقائي (Fallback) إلى `mode: "local_retrieval"` في حالة انقطاع النت أو غياب المفتاح.
4. **Phase 4: Deterministic Conclusions & Stale Protection (`conclusions.py`)**
   - صياغة إحصائية علمية حتمية بدون أي تدخل من الذكاء الاصطناعي (Zero-LLM).
   - حظر المصطلحات المضللة علمياً: منع كلمات "stable" أو "ثابت" واستبدالها دائماً بـ "الأدلة الإحصائية غير كافية على وجود اتجاه عام" عند $p \ge \alpha$.
   - تمثيل رسالة المسابقة الجوهرية ("What the Average Hides"): ذكر المقامات دائماً ونسب الخلايا المتزايدة والمتناقصة وغير المؤهلة للجودة.
   - حماية الطلبات المعلقة (`ActiveRequestTracker`): رفض أي رد قديم يصل متأخراً إذا قام المستخدم بتغيير المنطقة أو الفترة الزمنية في الـ UI.
5. **Phase 5: Unified Facade & Role 03 Adapter (`facade.py`)**
   - واجهة موحدة `Role04Service` توفر مدخلاً بسيطاً وسلساً لكافة عمليات الـ Q&A وتوليد الاستنتاجات.
   - محول مرن للبيانات `normalize_result_payload()` يقبل جميع مسميات الحقول الشائعة أو المختصرة من Role 02/03 ويحولها إلى العقد المعماري القياسي تلقائياً.

---

## 2. مصفوفة المسؤوليات بين أعضاء الفريق (Team Handover Matrix)

| الدور | المسؤولية الأساسية | ما يرسله إلى Role 04 / الـ API | ما يستقبله من Role 04 |
| :--- | :--- | :--- | :--- |
| **Role 01: Data & ETL Lead** | معالجة ملفات NetCDF/HDF وضبط الشبكات المكانية وتحديث سجل الجاهزية. | تحديث `runtime_catalog.json` و `scope.v2.json` ببيانات الجاهزية (`measurement_ready`, `app_available`, الفترات، الإصدارات). | يقرأ Role 04 هذه الملفات لحظياً لتقرير جاهزية البيانات بصدق دون تخزين الجاهزية داخل نصوص المقاطع. |
| **Role 02: Statistical ML Lead** | حسابات الاتجاهات الإحصائية (Mann-Kendall, Sen's slope, فترات الثقة، تصفية الجودة QA، وحساسية Spin-It). | مصفوفة أرقام إحصائية نقية في JSON (Slopes, $p$-values, عدد الخلايا المؤهلة والمحجوبة) ترسل إلى Role 03. | يحول `conclusions.py` هذه الأرقام إلى جمل علمية ثنائية اللغة محمية من الهلوسة بدون تغيير رقم واحد. |
| **Role 03: Backend API Lead** | إدارة سيرفر FastAPI وتوجيه الـ Endpoints (`/v1/explanations/ask`, `/v1/explanations/conclusions`) وإدارة البيئة. | تمرير استفسارات المستخدمين أو مخرجات Role 02 إلى كلاس `Role04Service` في `packages/rag/facade.py`. | استلام كائنات JSON موحدة تحتوي على النصوص، الاستشهادات الموثقة، شرائح الاستنتاج التفاعلية، وحالة الجاهزية. |
| **Role 05 & 06: Frontend & UI/UX Leads** | الخريطة التفاعلية، الرسوم البيانية الزمنية، درج الأسئلة والأجوبة، وأزرار شرائح الاستنتاج. | إرسال أسئلة المستخدم، كود المنطقة `region_id`، الفترة الزمنية `period`، واللغة `ar`/`en`، مع تتبع `request_id`. | رندر شرائح الاستنتاج، تنفيذ إجراءات الخريطة المقترنة (`FOCUS_REGION`, `REVEAL_CELLS`, إلخ)، وعرض روابط الاستشهادات. |

---

## 3. دليل الربط لـ Role 01 (Data & Catalog Lead)

* **المعرفات المعمارية القياسية (Canonical Variable IDs):**
  يجب دائماً استخدام المعرفات الأربعة المعتمدة في `docs/architecture/scope.v2.json`:
  - `air_temperature` (الخاص بمنتج MERRA-2 `T2M`)
  - `soil_moisture` (الخاص بمنتج GLDAS `SoilMoi0_10cm_inst`)
  - `precipitation` (الخاص بمنتج GPM IMERG `GPM_3IMERGM`)
  - `vegetation_greenness` (الخاص بمنتج MODIS `MOD13C2` أو `ndvi`)  
  *(ملاحظة: يقوم Role 04 بربط المعرفات القديمة مثل `T2M` و `ndvi` تلقائياً)*.
* **تفعيل جاهزية التطبيق الحية (App Availability):**
  حالياً، جميع المكعبات الـ 12 جاهزة قياسياً (`measurement_ready: true`) ولكن جاهزية التطبيق `app_available: false`. بمجرد رفع الـ API للمكعب، قم بتعديل `"app_available": true` في ملف `data/nasa/runtime_catalog.json` ليتحول الرد في Role 04 تلقائياً من `documented_only` إلى `recommended`.
* **عزل وحدات القياس:**
  ملف `cairo_temperature_monthly.csv` يمثل قياسات محطة نقطية لناسا POWER بالسيليزيوس، وهو معزول تماماً عن شبكة MERRA-2 المقاسة بالكلفن.

---

## 4. دليل الربط لـ Role 02 (Statistical ML Lead)

> **رسالة لزميلنا في Role 02:**  
> إنت مسؤول عن الأرقام والمعادلات الرياضية فقط (Mann-Kendall, Sen's Slope, Confidence Intervals, QA Masking). ابعت الأرقام دي في JSON لـ Role 03، وموديول الاستنتاجات عندنا (`conclusions.py`) هيحولها لجمل علمية منضبطة بالعربي والإنجليزي من غير ما يقرب للذكاء الاصطناعي نهائياً، وهيحترم حالات الـ `null` لو العينة غير كافية أو التباين صفر!

### الحقول الإحصائية المقبولة في الـ JSON:

```json
{
  "analysis_id": "ana_nile_t2m_2001_2024",
  "request_id": "req_0042",
  "variable_id": "air_temperature",
  "region_id": "nile_corridor",
  "period": { "start_year": 2001, "end_year": 2024 },
  "product_version": "5.12.4",
  "regional_trend": {
    "sen_slope": 0.034,
    "slope_units": "K/year",
    "p_value": 0.008,
    "alpha": 0.05,
    "confidence_interval": [0.019, 0.049],
    "significant": true
  },
  "cell_distribution": {
    "total_cells": 1000,
    "eligible_cells": 950,
    "ineligible_qa_cells": 50,
    "increasing_cells": 620,
    "decreasing_cells": 45,
    "denominator_basis": "eligible_cells"
  },
  "artifacts": {
    "region_map": true,
    "regional_chart": true,
    "cell_map": true,
    "spin_it": true,
    "receipt": true
  }
}
```

* **مرونة الأسماء:** يقبل المحول `normalize_result_payload()` الأسماء البديلة تلقائياً مثل `slope` بدل `sen_slope`، و `p` بدل `p_value`، و `result_id` بدل `analysis_id`، و `masked_cells` بدل `ineligible_qa_cells`.

---

## 5. دليل الربط لـ Role 03 (Backend API Lead)

> **رسالة لزميلنا في Role 03:**  
> كل اللي هتعمله في سيرفر FastAPI إنك تستدعي كلاس `Role04Service` من `packages/rag/facade.py`. لو مفتاح `GEMINI_API_KEY` موجود في `.env` هيشتغل Gemini ويعدي على صمام الأمان (Validator)، ولو مش موجود أو النت فصل هيرد أوتوماتيك بـ `local_retrieval` من غير ما يرمي أي Exception أو يعطل السيرفر!

### كود البايثون الجاهز للربط مع FastAPI:

```python
# app/routers/rag_router.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from packages.rag.facade import Role04Service, normalize_result_payload

router = APIRouter(prefix="/v1/explanations", tags=["RAG & Explanations"])

# إنشاء نسخة مفردة (Singleton) عند إقلاع السيرفر
rag_service = Role04Service()

class QuestionRequest(BaseModel):
    query: str
    region_id: Optional[str] = None
    period: Optional[List[str]] = None
    language: Optional[str] = "ar"

@router.post("/ask")
def ask_concept_question(payload: QuestionRequest):
    """مسار الأسئلة والمفاهيم العلمية (Concept Q&A)"""
    try:
        result = rag_service.answer_question(
            query=payload.query,
            region_id=payload.region_id,
            period=tuple(payload.period) if payload.period else None,
            language=payload.language
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.post("/conclusions")
def generate_statistical_conclusions(raw_payload: Dict[str, Any], language: str = "ar"):
    """مسار الاستنتاجات الإحصائية التفاعلية (Deterministic Statistical Conclusions)"""
    try:
        # تسجيل الطلب لحماية الـ UI من الطلبات القديمة المتأخرة
        req_id = raw_payload.get("request_id")
        ana_id = raw_payload.get("analysis_id") or raw_payload.get("result_id")
        if req_id and ana_id:
            rag_service.register_analysis(
                request_id=req_id,
                analysis_id=ana_id,
                variable_id=raw_payload.get("variable_id"),
                region_id=raw_payload.get("region_id")
            )
        
        # تحويل البيانات واستخراج الشرائح
        result = rag_service.render_result(raw_payload, language=language, normalize=True)
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.post("/reset-session")
def reset_session():
    """إعادة تعيين الجلسة عند عمل Reset للواجهة"""
    rag_service.reset_session()
    return {"status": "session_reset"}
```

---

## 6. دليل الربط لـ Roles 05 & 06 (Frontend & UI/UX Leads)

> **رسالة لزملائنا في Frontend:**  
> إنتوا هتتعاملوا مع نوعين من الردود:  
> 1. **رد شات الأسئلة العلمية:** بيجيلكم فيه حالة السؤال (`status`) والإجابة والمصادر الموثقة مع الـ URLs وروابط NASA CMR.  
> 2. **شرائح الاستنتاج التفاعلية على الخريطة:** بيجيلكم مصفوفة شرائح (`segments[]`)، كل شريحة فيها النص بالعربي والإنجليزي، وزرار أكشن جاهز (`action`) عشان لما المستخدم يضغط عليه الخريطة تعمل Zoom أو تفتح الـ Heatmap أو الـ Slider تلقائياً!

### كود React / TypeScript الكامل لاستقبال وعرض الاستنتاجات والأكشنز:

```tsx
// components/InteractiveConclusionsBar.tsx
import React, { useState } from 'react';

export interface ConclusionSegment {
  segment_id: string;
  type: 'scope_context' | 'regional_trend' | 'spatial_distribution' | 'sensitivity' | 'provenance';
  text_ar: string;
  text_en: string;
  action?: 'FOCUS_REGION' | 'FOCUS_REGIONAL_CHART' | 'REVEAL_CELLS' | 'OPEN_SPIN_IT' | 'OPEN_RECEIPT';
  action_label_ar?: string;
  action_label_en?: string;
}

export interface ConclusionResponse {
  status: 'ok' | 'stale_response' | 'error';
  mode: 'deterministic_template';
  analysis_id: string;
  request_id: string;
  language: 'ar' | 'en';
  segments: ConclusionSegment[];
}

interface Props {
  data: ConclusionResponse;
  language: 'ar' | 'en';
  onExecuteAction: (action: string) => void;
}

export const InteractiveConclusionsBar: React.FC<Props> = ({ data, language, onExecuteAction }) => {
  // حماية من الردود القديمة
  if (data.status === 'stale_response' || !data.segments?.length) {
    return null; // تجاهل الرد إذا كان قديماً واليوزر اختار منطقة أخرى
  }

  return (
    <div className="conclusions-container" dir={language === 'ar' ? 'rtl' : 'ltr'}>
      <h3 className="text-xl font-bold mb-4">
        {language === 'ar' ? '📊 الاستنتاجات العلمية التفاعلية' : '📊 Interactive Scientific Conclusions'}
      </h3>
      
      <div className="space-y-4">
        {data.segments.map((seg) => (
          <div key={seg.segment_id} className="p-4 bg-slate-900 border border-slate-800 rounded-lg flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <p className="text-slate-200 leading-relaxed">
              {language === 'ar' ? seg.text_ar : seg.text_en}
            </p>

            {seg.action && (
              <button
                onClick={() => onExecuteAction(seg.action!)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-md shadow transition whitespace-nowrap"
              >
                {language === 'ar' ? seg.action_label_ar : seg.action_label_en}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
```

### جدول إجراءات الأزرار في الواجهة (Frontend Actions Dictionary):

| Action Enum | مكان الاستخدام | ما يجب أن تنفذه الواجهة عند النقر |
| :--- | :--- | :--- |
| `FOCUS_REGION` | شريحة النطاق والمنطقة | عمل Pan/Zoom على حدود المنطقة المحددة (`region_id`) وإبراز المضلع (Polygon). |
| `FOCUS_REGIONAL_CHART` | شريحة الاتجاه العام | التمرير إلى الرسم البياني الزمني للمنطقة وإبراز خط الاتجاه وفترة الثقة. |
| `REVEAL_CELLS` | شريحة "ما يخفيه المتوسط" | تبديل طبقة الخريطة لعرض الـ Heatmap وتوزيع الخلايا المتزايدة والمتناقصة. |
| `OPEN_SPIN_IT` | شريحة تحليل الحساسية | فتح نافذة الـ Slider التفاعلي (Spin-It) لاختبار تغيير سنوات البداية والنهاية. |
| `OPEN_RECEIPT` | شريحة التوثيق والمصادر | فتح نافذة التوثيق (Provenance Receipt) لعرض أرقام الإصدارات وبصمات SHA-256. |

---

## 7. قائمة التحقق السريعة للاختبار (Judge Demo & Verification)

للتأكد من عمل كافة أجزاء النظام محلياً بدون نت وبدون مفاتيح:
1. **تشغيل كامل الاختبارات الـ 170:**
   ```powershell
   python -m pytest tests -q
   ```
   *(النتيجة المتوقعة: 170 passed في أقل من 7 ثوانٍ)*.
2. **تجربة الـ CLI للبحث الدلالي مباشرة:**
   ```powershell
   python data/nasa/rag/retrieve.py "هل الدلتا بتسخن؟" --region nile_corridor
   ```
3. **مراجعة وثيقة العرض للجنة التحكيم (Pitch Script & AI Disclosure):**  
   موجودة في الرابط: [`docs/ROLE_04_PITCH_AND_DISCLOSURE.md`](file:///d:/nasa_planet/docs/ROLE_04_PITCH_AND_DISCLOSURE.md).
