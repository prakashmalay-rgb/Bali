import { useState } from "react";
import { API_BASE_URL } from "../../api/apiClient";

const STEPS = [
  "Villa Info",
  "Property Details",
  "Amenities",
  "Services",
  "Target Guests",
  "Pricing",
  "Contact Person",
  "Bank Details",
  "Documents",
  "Review & Submit",
];

const BALI_AREAS = [
  "Canggu", "Seminyak", "Kuta", "Legian", "Ubud",
  "Jimbaran", "Nusa Dua", "Uluwatu", "Sanur", "Denpasar", "Other",
];

const INDONESIAN_BANKS = [
  "BCA", "BNI", "BRI", "Mandiri", "CIMB Niaga", "Danamon",
  "Permata", "BTN", "BSI", "Bank Jago", "SeaBank", "Other",
];

const initialForm = {
  // Step 1
  villa_name: "", address: "", area: "",
  // Step 2
  property_type: "Villa", num_rooms: "", max_guests: "", year_established: "",
  // Step 3
  amenities: [],
  // Step 4
  services: [],
  // Step 5
  target_guests: [],
  // Step 6
  rate_min: "", rate_max: "", commission: "15", agreed_to_terms: false,
  // Step 7
  contact_name: "", contact_role: "", contact_phone: "", contact_email: "",
  // Step 8
  bank_name: "", account_holder: "", account_number: "",
  // Step 9
  business_reg: "", website: "", instagram: "", photo_url: "",
};

const AMENITY_OPTIONS = [
  "Swimming Pool", "WiFi", "Air Conditioning", "Full Kitchen",
  "Parking", "Garden", "Gym / Fitness", "Spa Facilities", "BBQ Area", "Laundry",
];

const SERVICE_OPTIONS = [
  "Massage / Spa", "Transportation / Driver", "Guided Tours",
  "Private Chef", "Laundry Service", "Airport Transfer",
  "Cooking Class", "Yoga Sessions", "Bicycle Rental", "Concierge",
];

const GUEST_OPTIONS = [
  "Couples", "Families with Children", "Solo Travellers",
  "Groups / Events", "Honeymoon Couples", "Digital Nomads", "Luxury Seekers",
];

function CheckboxGroup({ options, selected, onChange }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
      {options.map((opt) => (
        <label
          key={opt}
          className={`flex items-center gap-2 px-3 py-2.5 rounded-[14px] border cursor-pointer transition-all text-[14px] font-medium select-none ${
            selected.includes(opt)
              ? "border-[#FF8000] bg-[#FFF5EB] text-[#FF8000]"
              : "border-gray-200 bg-white text-gray-700 hover:border-gray-400"
          }`}
        >
          <input
            type="checkbox"
            className="hidden"
            checked={selected.includes(opt)}
            onChange={() => onChange(opt)}
          />
          <span className={`w-4 h-4 rounded-[4px] border flex items-center justify-center flex-shrink-0 transition-all ${
            selected.includes(opt) ? "border-[#FF8000] bg-[#FF8000]" : "border-gray-300"
          }`}>
            {selected.includes(opt) && (
              <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                <path d="M1 4L3.5 6.5L9 1" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            )}
          </span>
          {opt}
        </label>
      ))}
    </div>
  );
}

function InputField({ label, required, ...props }) {
  return (
    <div className="relative">
      {label && (
        <label className="absolute -top-2.5 left-3 bg-white px-2 text-[13px] sm:text-[14px] font-semibold text-gray-800 z-10">
          {label}{required && <span className="text-red-500 ml-0.5">*</span>}
        </label>
      )}
      <input
        {...props}
        className="w-full h-[52px] sm:h-[60px] px-4 sm:px-5 py-3 border border-gray-300 rounded-[16px] focus:outline-none focus:border-[#FF8000] text-black bg-white text-[15px] transition-colors"
      />
    </div>
  );
}

function SelectField({ label, required, children, ...props }) {
  return (
    <div className="relative">
      {label && (
        <label className="absolute -top-2.5 left-3 bg-white px-2 text-[13px] sm:text-[14px] font-semibold text-gray-800 z-10">
          {label}{required && <span className="text-red-500 ml-0.5">*</span>}
        </label>
      )}
      <select
        {...props}
        className="w-full h-[52px] sm:h-[60px] px-4 sm:px-5 py-3 border border-gray-300 rounded-[16px] focus:outline-none focus:border-[#FF8000] text-black bg-white text-[15px] appearance-none cursor-pointer transition-colors"
      >
        {children}
      </select>
    </div>
  );
}

export default function VillaPartnershipForm({ onClose }) {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState(initialForm);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  const set = (key, value) => setForm((f) => ({ ...f, [key]: value }));

  const toggleArray = (key, value) => {
    setForm((f) => ({
      ...f,
      [key]: f[key].includes(value)
        ? f[key].filter((v) => v !== value)
        : [...f[key], value],
    }));
  };

  const handleNext = () => {
    setError("");
    if (!validateStep()) return;
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  };

  const handleBack = () => {
    setError("");
    setStep((s) => Math.max(s - 1, 0));
  };

  const validateStep = () => {
    if (step === 0) {
      if (!form.villa_name.trim()) { setError("Villa name is required."); return false; }
      if (!form.address.trim()) { setError("Address is required."); return false; }
      if (!form.area) { setError("Please select an area."); return false; }
    }
    if (step === 1) {
      if (!form.num_rooms || isNaN(form.num_rooms)) { setError("Number of rooms is required."); return false; }
      if (!form.max_guests || isNaN(form.max_guests)) { setError("Max guests is required."); return false; }
    }
    if (step === 5) {
      if (!form.rate_min || !form.rate_max) { setError("Please enter rate range."); return false; }
      if (!form.agreed_to_terms) { setError("Please agree to EasyBali terms."); return false; }
    }
    if (step === 6) {
      if (!form.contact_name.trim()) { setError("Contact name is required."); return false; }
      if (!form.contact_phone.trim()) { setError("Contact phone is required."); return false; }
      if (!form.contact_email.trim() || !form.contact_email.includes("@")) { setError("Valid email is required."); return false; }
    }
    if (step === 7) {
      if (!form.bank_name) { setError("Please select a bank."); return false; }
      if (!form.account_holder.trim()) { setError("Account holder name is required."); return false; }
      if (!form.account_number.trim()) { setError("Account number is required."); return false; }
    }
    return true;
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE_URL}/onboarding/apply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Server error ${res.status}`);
      }
      setSuccess(true);
    } catch (err) {
      setError(err.message || "Submission failed. Please try again or contact us directly.");
    } finally {
      setSubmitting(false);
    }
  };

  const stepContent = () => {
    switch (step) {
      case 0:
        return (
          <div className="flex flex-col gap-5">
            <InputField label="Villa Name" required placeholder="e.g. Villa Bali Indah" value={form.villa_name} onChange={(e) => set("villa_name", e.target.value)} />
            <InputField label="Full Address" required placeholder="Street, village, district" value={form.address} onChange={(e) => set("address", e.target.value)} />
            <SelectField label="Area in Bali" required value={form.area} onChange={(e) => set("area", e.target.value)}>
              <option value="">Select area...</option>
              {BALI_AREAS.map((a) => <option key={a} value={a}>{a}</option>)}
            </SelectField>
          </div>
        );
      case 1:
        return (
          <div className="flex flex-col gap-5">
            <SelectField label="Property Type" value={form.property_type} onChange={(e) => set("property_type", e.target.value)}>
              {["Villa", "Resort", "Boutique Hotel", "Guesthouse", "Private Estate"].map((t) => <option key={t} value={t}>{t}</option>)}
            </SelectField>
            <div className="grid grid-cols-2 gap-4">
              <InputField label="No. of Rooms / Units" required type="number" min="1" placeholder="e.g. 5" value={form.num_rooms} onChange={(e) => set("num_rooms", e.target.value)} />
              <InputField label="Max Guests" required type="number" min="1" placeholder="e.g. 20" value={form.max_guests} onChange={(e) => set("max_guests", e.target.value)} />
            </div>
            <InputField label="Year Established" type="number" min="1900" max="2026" placeholder="e.g. 2018" value={form.year_established} onChange={(e) => set("year_established", e.target.value)} />
          </div>
        );
      case 2:
        return (
          <div className="flex flex-col gap-4">
            <p className="text-gray-500 text-[14px]">Select all amenities available at your property.</p>
            <CheckboxGroup options={AMENITY_OPTIONS} selected={form.amenities} onChange={(v) => toggleArray("amenities", v)} />
          </div>
        );
      case 3:
        return (
          <div className="flex flex-col gap-4">
            <p className="text-gray-500 text-[14px]">Which services can your guests book through EasyBali?</p>
            <CheckboxGroup options={SERVICE_OPTIONS} selected={form.services} onChange={(v) => toggleArray("services", v)} />
          </div>
        );
      case 4:
        return (
          <div className="flex flex-col gap-4">
            <p className="text-gray-500 text-[14px]">Who typically stays at your property?</p>
            <CheckboxGroup options={GUEST_OPTIONS} selected={form.target_guests} onChange={(v) => toggleArray("target_guests", v)} />
          </div>
        );
      case 5:
        return (
          <div className="flex flex-col gap-5">
            <p className="text-gray-500 text-[14px]">Set your nightly rate range (IDR) and preferred commission.</p>
            <div className="grid grid-cols-2 gap-4">
              <InputField label="Min Rate (IDR)" required type="number" placeholder="e.g. 1500000" value={form.rate_min} onChange={(e) => set("rate_min", e.target.value)} />
              <InputField label="Max Rate (IDR)" required type="number" placeholder="e.g. 5000000" value={form.rate_max} onChange={(e) => set("rate_max", e.target.value)} />
            </div>
            <SelectField label="Commission Rate" value={form.commission} onChange={(e) => set("commission", e.target.value)}>
              <option value="10">10% — Basic</option>
              <option value="15">15% — Standard (Recommended)</option>
              <option value="20">20% — Premium Visibility</option>
            </SelectField>
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                className="mt-1 w-4 h-4 accent-[#FF8000] flex-shrink-0"
                checked={form.agreed_to_terms}
                onChange={(e) => set("agreed_to_terms", e.target.checked)}
              />
              <span className="text-[13px] text-gray-600">
                I agree to EasyBali's{" "}
                <a href="/terms-and-conditions" target="_blank" className="text-[#FF8000] underline">Terms & Conditions</a>{" "}
                and commission structure. <span className="text-red-500">*</span>
              </span>
            </label>
          </div>
        );
      case 6:
        return (
          <div className="flex flex-col gap-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <InputField label="Full Name" required placeholder="Contact person's full name" value={form.contact_name} onChange={(e) => set("contact_name", e.target.value)} />
              <InputField label="Role / Title" placeholder="e.g. Manager, Owner" value={form.contact_role} onChange={(e) => set("contact_role", e.target.value)} />
            </div>
            <InputField label="WhatsApp / Phone" required type="tel" placeholder="+62 812 3456 7890" value={form.contact_phone} onChange={(e) => set("contact_phone", e.target.value)} />
            <InputField label="Email Address" required type="email" placeholder="you@villa.com" value={form.contact_email} onChange={(e) => set("contact_email", e.target.value)} />
          </div>
        );
      case 7:
        return (
          <div className="flex flex-col gap-5">
            <p className="text-gray-500 text-[14px]">These details are used for disbursing your share of payments.</p>
            <SelectField label="Bank Name" required value={form.bank_name} onChange={(e) => set("bank_name", e.target.value)}>
              <option value="">Select bank...</option>
              {INDONESIAN_BANKS.map((b) => <option key={b} value={b}>{b}</option>)}
            </SelectField>
            <InputField label="Account Holder Name" required placeholder="As printed on bank account" value={form.account_holder} onChange={(e) => set("account_holder", e.target.value)} />
            <InputField label="Account Number" required placeholder="e.g. 1234567890" value={form.account_number} onChange={(e) => set("account_number", e.target.value)} />
          </div>
        );
      case 8:
        return (
          <div className="flex flex-col gap-5">
            <p className="text-gray-500 text-[14px]">All fields optional but help us process your application faster.</p>
            <InputField label="Business Reg. No. / SIUP" placeholder="e.g. SIUP-1234/2020" value={form.business_reg} onChange={(e) => set("business_reg", e.target.value)} />
            <InputField label="Villa Website" type="url" placeholder="https://yourvillabali.com" value={form.website} onChange={(e) => set("website", e.target.value)} />
            <InputField label="Instagram Handle" placeholder="@yourvillabali" value={form.instagram} onChange={(e) => set("instagram", e.target.value)} />
            <InputField label="Villa Photo URL" type="url" placeholder="https://..." value={form.photo_url} onChange={(e) => set("photo_url", e.target.value)} />
          </div>
        );
      case 9:
        return (
          <div className="flex flex-col gap-4 text-[14px]">
            <p className="text-gray-500">Please review your application before submitting.</p>
            <div className="bg-gray-50 rounded-[20px] p-4 sm:p-6 flex flex-col gap-3">
              {[
                ["Villa", `${form.villa_name} — ${form.area}`],
                ["Address", form.address],
                ["Type", `${form.property_type}, ${form.num_rooms} rooms, max ${form.max_guests} guests`],
                ["Amenities", form.amenities.join(", ") || "—"],
                ["Services", form.services.join(", ") || "—"],
                ["Target Guests", form.target_guests.join(", ") || "—"],
                ["Rate Range", `IDR ${Number(form.rate_min).toLocaleString()} – IDR ${Number(form.rate_max).toLocaleString()}`],
                ["Commission", `${form.commission}%`],
                ["Contact", `${form.contact_name} (${form.contact_role}) • ${form.contact_phone} • ${form.contact_email}`],
                ["Bank", `${form.bank_name} — ${form.account_holder} — ${form.account_number}`],
                ["Business Reg.", form.business_reg || "—"],
              ].map(([label, value]) => (
                <div key={label} className="flex gap-2">
                  <span className="font-semibold text-gray-700 min-w-[100px] sm:min-w-[130px]">{label}:</span>
                  <span className="text-gray-600 break-all">{value}</span>
                </div>
              ))}
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-[30px] sm:rounded-[40px] w-full max-w-[560px] max-h-[90vh] overflow-y-auto shadow-[0_0_60px_rgba(0,0,0,0.25)] relative flex flex-col">

        {/* Close button */}
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 sm:top-5 sm:right-5 w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center text-gray-600 transition-colors z-10"
          aria-label="Close"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M1 1l12 12M13 1L1 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </button>

        {success ? (
          <div className="flex flex-col items-center justify-center gap-6 py-16 px-8 text-center">
            <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center">
              <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                <path d="M6 18L14 26L30 10" stroke="#22c55e" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900">Application Received!</h2>
            <p className="text-gray-500 text-[15px] leading-relaxed max-w-[360px]">
              Thank you, <strong>{form.contact_name || "partner"}</strong>! Our team will review your application for <strong>{form.villa_name}</strong> and contact you within 2–3 business days.
            </p>
            <button
              type="button"
              onClick={onClose}
              className="px-8 py-3 rounded-[50px] bg-[#FF8000] text-white font-semibold hover:bg-[#e67200] transition-colors"
            >
              Done
            </button>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="px-6 sm:px-8 pt-6 sm:pt-8 pb-4">
              <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Villa Partnership Application</h2>
              <p className="text-gray-500 text-[13px] sm:text-[14px] mt-1">
                Step {step + 1} of {STEPS.length} — <span className="font-semibold text-gray-700">{STEPS[step]}</span>
              </p>

              {/* Progress bar */}
              <div className="mt-4 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#FF8000] rounded-full transition-all duration-300"
                  style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
                />
              </div>

              {/* Step pills */}
              <div className="flex gap-1 mt-3 overflow-x-auto pb-1 scrollbar-hide">
                {STEPS.map((s, i) => (
                  <div
                    key={s}
                    className={`flex-shrink-0 px-2.5 py-1 rounded-full text-[11px] font-semibold transition-all ${
                      i === step
                        ? "bg-[#FF8000] text-white"
                        : i < step
                        ? "bg-orange-100 text-[#FF8000]"
                        : "bg-gray-100 text-gray-400"
                    }`}
                  >
                    {i + 1}. {s}
                  </div>
                ))}
              </div>
            </div>

            {/* Body */}
            <div className="flex-1 px-6 sm:px-8 py-4">
              {stepContent()}
              {error && (
                <p className="mt-4 text-red-500 text-[13px] font-medium">{error}</p>
              )}
            </div>

            {/* Footer nav */}
            <div className="px-6 sm:px-8 py-5 sm:py-6 border-t border-gray-100 flex items-center justify-between gap-4">
              <button
                type="button"
                onClick={handleBack}
                disabled={step === 0}
                className="px-5 py-2.5 rounded-[50px] border border-gray-300 text-gray-700 font-semibold text-[14px] hover:border-gray-400 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              >
                ← Back
              </button>

              {step < STEPS.length - 1 ? (
                <button
                  type="button"
                  onClick={handleNext}
                  className="px-6 py-2.5 rounded-[50px] bg-[#FF8000] text-white font-semibold text-[14px] hover:bg-[#e67200] transition-colors"
                >
                  Next →
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="px-6 py-2.5 rounded-[50px] bg-[#FF8000] text-white font-semibold text-[14px] hover:bg-[#e67200] transition-colors disabled:opacity-60 flex items-center gap-2"
                >
                  {submitting ? (
                    <>
                      <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                      Submitting...
                    </>
                  ) : "Submit Application"}
                </button>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
