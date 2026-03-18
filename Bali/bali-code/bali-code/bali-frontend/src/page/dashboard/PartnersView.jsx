import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API_BASE_URL } from "../../api/apiClient";
import {
    FiSearch, FiPhone, FiMail, FiEdit2, FiTrash2, FiCheck,
    FiX, FiEye, FiMessageSquare, FiRefreshCw, FiMapPin,
    FiUsers, FiDollarSign, FiHome, FiUser
} from "react-icons/fi";

const STATUS_CONFIG = {
    pending_review: { label: "Pending Review", color: "bg-yellow-100 text-yellow-700 border-yellow-200" },
    accepted: { label: "Accepted", color: "bg-green-100 text-green-700 border-green-200" },
    denied: { label: "Denied", color: "bg-red-100 text-red-700 border-red-200" },
};

const BALI_AREAS = ["Canggu", "Seminyak", "Kuta", "Legian", "Ubud", "Jimbaran", "Nusa Dua", "Uluwatu", "Sanur", "Denpasar", "Other"];
const INDONESIAN_BANKS = ["BCA", "BNI", "BRI", "Mandiri", "CIMB Niaga", "Danamon", "Permata", "BTN", "BSI", "Bank Jago", "SeaBank", "Other"];
const AMENITY_OPTIONS = ["Swimming Pool", "WiFi", "Air Conditioning", "Full Kitchen", "Parking", "Garden", "Gym / Fitness", "Spa Facilities", "BBQ Area", "Laundry"];
const SERVICE_OPTIONS = ["Massage / Spa", "Transportation / Driver", "Guided Tours", "Private Chef", "Laundry Service", "Airport Transfer", "Cooking Class", "Yoga Sessions", "Bicycle Rental", "Concierge"];
const GUEST_OPTIONS = ["Couples", "Families with Children", "Solo Travellers", "Groups / Events", "Honeymoon Couples", "Digital Nomads", "Luxury Seekers"];

function StatCard({ label, value, color }) {
    return (
        <div className={`bg-white rounded-2xl px-5 py-4 border ${color} flex flex-col gap-1 min-w-[120px]`}>
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">{label}</p>
            <p className="text-3xl font-bold text-gray-900">{value ?? "—"}</p>
        </div>
    );
}

function StatusBadge({ status }) {
    const cfg = STATUS_CONFIG[status] || { label: status, color: "bg-gray-100 text-gray-600 border-gray-200" };
    return (
        <span className={`inline-block px-2.5 py-1 rounded-full text-xs font-bold border ${cfg.color}`}>
            {cfg.label}
        </span>
    );
}

function CheckboxDisplay({ items }) {
    if (!items || items.length === 0) return <span className="text-gray-400 text-sm">—</span>;
    return (
        <div className="flex flex-wrap gap-1.5">
            {items.map((item) => (
                <span key={item} className="px-2 py-0.5 bg-orange-50 text-orange-700 rounded-full text-xs font-medium border border-orange-100">
                    {item}
                </span>
            ))}
        </div>
    );
}

// ─── Detail Modal ─────────────────────────────────────────────────────────────
function DetailModal({ app, onClose, onStatusChange, onEdit }) {
    const [note, setNote] = useState(app.admin_note || "");
    const [updating, setUpdating] = useState(false);

    const updateStatus = async (status) => {
        setUpdating(true);
        try {
            await axios.put(
                `${API_BASE_URL}/dashboard-api/partners/${app.application_id}/status`,
                { status, admin_note: note },
                { headers: { Authorization: `Bearer ${localStorage.getItem("easybali_token")}` } }
            );
            onStatusChange();
            onClose();
        } catch (e) {
            alert("Failed to update status");
        } finally {
            setUpdating(false);
        }
    };

    const Section = ({ title, children }) => (
        <div className="mb-5">
            <h4 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-3">{title}</h4>
            {children}
        </div>
    );

    const Row = ({ label, value }) => (
        <div className="flex gap-2 mb-2">
            <span className="text-sm font-semibold text-gray-600 min-w-[140px]">{label}:</span>
            <span className="text-sm text-gray-800 break-all">{value || "—"}</span>
        </div>
    );

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-[24px] w-full max-w-[680px] max-h-[90vh] overflow-y-auto shadow-2xl flex flex-col">
                <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between rounded-t-[24px] z-10">
                    <div>
                        <h2 className="text-lg font-bold text-gray-900">{app.villa_name}</h2>
                        <p className="text-xs text-gray-500 mt-0.5">Application ID: {app.application_id} · Submitted {app.submitted_at ? new Date(app.submitted_at).toLocaleDateString() : "—"}</p>
                    </div>
                    <div className="flex items-center gap-2">
                        <StatusBadge status={app.status} />
                        <button onClick={onClose} className="w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center text-gray-600 transition-colors ml-2">
                            <FiX size={14} />
                        </button>
                    </div>
                </div>

                <div className="p-6">
                    <Section title="Property">
                        <Row label="Villa Name" value={app.villa_name} />
                        <Row label="Address" value={app.address} />
                        <Row label="Area" value={app.area} />
                        <Row label="Property Type" value={app.property_type} />
                        <Row label="Rooms / Units" value={app.num_rooms} />
                        <Row label="Max Guests" value={app.max_guests} />
                        <Row label="Year Established" value={app.year_established} />
                    </Section>

                    <Section title="Amenities & Services">
                        <div className="mb-2">
                            <p className="text-xs font-semibold text-gray-500 mb-1.5">Amenities</p>
                            <CheckboxDisplay items={app.amenities} />
                        </div>
                        <div className="mt-3">
                            <p className="text-xs font-semibold text-gray-500 mb-1.5">Services Offered</p>
                            <CheckboxDisplay items={app.services} />
                        </div>
                        <div className="mt-3">
                            <p className="text-xs font-semibold text-gray-500 mb-1.5">Target Guests</p>
                            <CheckboxDisplay items={app.target_guests} />
                        </div>
                    </Section>

                    <Section title="Pricing & Commission">
                        <Row label="Rate Range" value={app.rate_min && app.rate_max ? `IDR ${Number(app.rate_min).toLocaleString()} – IDR ${Number(app.rate_max).toLocaleString()}` : "—"} />
                        <Row label="Commission" value={app.commission ? `${app.commission}%` : "—"} />
                    </Section>

                    <Section title="Contact">
                        <Row label="Name" value={app.contact_name} />
                        <Row label="Role" value={app.contact_role} />
                        <Row label="Phone" value={app.contact_phone} />
                        <Row label="Email" value={app.contact_email} />
                    </Section>

                    <Section title="Bank Details">
                        <Row label="Bank" value={app.bank_name} />
                        <Row label="Account Holder" value={app.account_holder} />
                        <Row label="Account Number" value={app.account_number} />
                    </Section>

                    <Section title="Documents & Online">
                        <Row label="Business Reg. No." value={app.business_reg} />
                        <Row label="Website" value={app.website} />
                        <Row label="Instagram" value={app.instagram} />
                        <Row label="Photo URL" value={app.photo_url} />
                    </Section>

                    {app.reviewed_by && (
                        <Section title="Review History">
                            <Row label="Reviewed By" value={app.reviewed_by} />
                            <Row label="Reviewed At" value={app.reviewed_at ? new Date(app.reviewed_at).toLocaleString() : "—"} />
                            <Row label="Admin Note" value={app.admin_note} />
                        </Section>
                    )}

                    {/* Admin Note */}
                    <div className="mt-2 mb-5">
                        <label className="text-xs font-semibold text-gray-600 block mb-1.5">Admin Note (optional)</label>
                        <textarea
                            className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-primary resize-none"
                            rows={2}
                            value={note}
                            onChange={(e) => setNote(e.target.value)}
                            placeholder="Add a note visible only to admins..."
                        />
                    </div>

                    {/* Action buttons */}
                    <div className="flex flex-wrap gap-2 pt-4 border-t border-gray-100">
                        {app.status !== "accepted" && (
                            <button
                                onClick={() => updateStatus("accepted")}
                                disabled={updating}
                                className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-xl text-sm font-semibold hover:bg-green-600 transition-colors disabled:opacity-60"
                            >
                                <FiCheck size={14} /> Accept
                            </button>
                        )}
                        {app.status !== "denied" && (
                            <button
                                onClick={() => updateStatus("denied")}
                                disabled={updating}
                                className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-xl text-sm font-semibold hover:bg-red-600 transition-colors disabled:opacity-60"
                            >
                                <FiX size={14} /> Deny
                            </button>
                        )}
                        {app.status !== "pending_review" && (
                            <button
                                onClick={() => updateStatus("pending_review")}
                                disabled={updating}
                                className="flex items-center gap-2 px-4 py-2 bg-yellow-400 text-white rounded-xl text-sm font-semibold hover:bg-yellow-500 transition-colors disabled:opacity-60"
                            >
                                <FiRefreshCw size={14} /> Set Pending
                            </button>
                        )}
                        <button
                            onClick={() => { onClose(); onEdit(app); }}
                            className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-xl text-sm font-semibold hover:bg-blue-600 transition-colors"
                        >
                            <FiEdit2 size={14} /> Edit
                        </button>
                        {app.contact_phone && (
                            <a
                                href={`tel:${app.contact_phone}`}
                                className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-xl text-sm font-semibold hover:bg-gray-200 transition-colors"
                            >
                                <FiPhone size={14} /> Call
                            </a>
                        )}
                        {app.contact_phone && (
                            <a
                                href={`https://wa.me/${app.contact_phone.replace(/\D/g, "")}`}
                                target="_blank"
                                rel="noreferrer"
                                className="flex items-center gap-2 px-4 py-2 bg-green-100 text-green-700 rounded-xl text-sm font-semibold hover:bg-green-200 transition-colors"
                            >
                                <FiMessageSquare size={14} /> WhatsApp
                            </a>
                        )}
                        {app.contact_email && (
                            <a
                                href={`mailto:${app.contact_email}`}
                                className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-xl text-sm font-semibold hover:bg-gray-200 transition-colors"
                            >
                                <FiMail size={14} /> Email
                            </a>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

// ─── Edit Modal ───────────────────────────────────────────────────────────────
function EditModal({ app, onClose, onSaved }) {
    const [form, setForm] = useState({ ...app });
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");

    const set = (key, val) => setForm((f) => ({ ...f, [key]: val }));
    const toggleArr = (key, val) => setForm((f) => ({
        ...f,
        [key]: f[key]?.includes(val) ? f[key].filter((v) => v !== val) : [...(f[key] || []), val]
    }));

    const handleSave = async () => {
        setSaving(true);
        setError("");
        try {
            await axios.put(
                `${API_BASE_URL}/dashboard-api/partners/${app.application_id}`,
                form,
                { headers: { Authorization: `Bearer ${localStorage.getItem("easybali_token")}` } }
            );
            onSaved();
            onClose();
        } catch (e) {
            setError("Failed to save changes");
        } finally {
            setSaving(false);
        }
    };

    const Field = ({ label, name, type = "text", ...rest }) => (
        <div className="flex flex-col gap-1">
            <label className="text-xs font-semibold text-gray-600">{label}</label>
            <input
                type={type}
                value={form[name] || ""}
                onChange={(e) => set(name, e.target.value)}
                className="border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-primary"
                {...rest}
            />
        </div>
    );

    const SelectField = ({ label, name, options }) => (
        <div className="flex flex-col gap-1">
            <label className="text-xs font-semibold text-gray-600">{label}</label>
            <select
                value={form[name] || ""}
                onChange={(e) => set(name, e.target.value)}
                className="border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-primary bg-white"
            >
                {options.map((o) => <option key={o} value={o}>{o}</option>)}
            </select>
        </div>
    );

    const CheckboxGroup = ({ label, name, options }) => (
        <div>
            <p className="text-xs font-semibold text-gray-600 mb-2">{label}</p>
            <div className="flex flex-wrap gap-2">
                {options.map((opt) => {
                    const checked = (form[name] || []).includes(opt);
                    return (
                        <button
                            key={opt}
                            type="button"
                            onClick={() => toggleArr(name, opt)}
                            className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-all ${
                                checked ? "bg-orange-100 text-orange-700 border-orange-300" : "bg-gray-50 text-gray-600 border-gray-200 hover:border-gray-400"
                            }`}
                        >
                            {opt}
                        </button>
                    );
                })}
            </div>
        </div>
    );

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-[24px] w-full max-w-[640px] max-h-[90vh] overflow-y-auto shadow-2xl">
                <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between rounded-t-[24px] z-10">
                    <h2 className="text-lg font-bold text-gray-900">Edit Application — {app.villa_name}</h2>
                    <button onClick={onClose} className="w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center text-gray-600 transition-colors">
                        <FiX size={14} />
                    </button>
                </div>

                <div className="p-6 flex flex-col gap-5">
                    <div className="grid grid-cols-2 gap-4">
                        <Field label="Villa Name" name="villa_name" />
                        <SelectField label="Area" name="area" options={["", ...BALI_AREAS]} />
                    </div>
                    <Field label="Address" name="address" />
                    <div className="grid grid-cols-3 gap-3">
                        <Field label="Rooms" name="num_rooms" type="number" />
                        <Field label="Max Guests" name="max_guests" type="number" />
                        <Field label="Year Est." name="year_established" type="number" />
                    </div>

                    <CheckboxGroup label="Amenities" name="amenities" options={AMENITY_OPTIONS} />
                    <CheckboxGroup label="Services" name="services" options={SERVICE_OPTIONS} />
                    <CheckboxGroup label="Target Guests" name="target_guests" options={GUEST_OPTIONS} />

                    <div className="grid grid-cols-3 gap-3">
                        <Field label="Min Rate (IDR)" name="rate_min" type="number" />
                        <Field label="Max Rate (IDR)" name="rate_max" type="number" />
                        <SelectField label="Commission %" name="commission" options={["10", "15", "20"]} />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <Field label="Contact Name" name="contact_name" />
                        <Field label="Contact Role" name="contact_role" />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <Field label="Phone" name="contact_phone" />
                        <Field label="Email" name="contact_email" type="email" />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <SelectField label="Bank" name="bank_name" options={["", ...INDONESIAN_BANKS]} />
                        <Field label="Account Holder" name="account_holder" />
                    </div>
                    <Field label="Account Number" name="account_number" />

                    <div className="grid grid-cols-2 gap-4">
                        <Field label="Business Reg. No." name="business_reg" />
                        <Field label="Instagram" name="instagram" />
                    </div>
                    <Field label="Website" name="website" />

                    {error && <p className="text-red-500 text-sm">{error}</p>}

                    <div className="flex gap-3 pt-2 border-t border-gray-100">
                        <button
                            onClick={handleSave}
                            disabled={saving}
                            className="flex-1 py-2.5 bg-primary text-white rounded-xl font-semibold text-sm hover:bg-blue-600 transition-colors disabled:opacity-60"
                        >
                            {saving ? "Saving..." : "Save Changes"}
                        </button>
                        <button
                            onClick={onClose}
                            className="px-5 py-2.5 border border-gray-200 text-gray-600 rounded-xl font-semibold text-sm hover:bg-gray-50 transition-colors"
                        >
                            Cancel
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function PartnersView() {
    const [applications, setApplications] = useState([]);
    const [counts, setCounts] = useState({});
    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState("all");
    const [search, setSearch] = useState("");
    const [viewApp, setViewApp] = useState(null);
    const [editApp, setEditApp] = useState(null);
    const [deleting, setDeleting] = useState(null);

    const fetchApplications = useCallback(async () => {
        setLoading(true);
        try {
            const params = {};
            if (statusFilter !== "all") params.status = statusFilter;
            if (search.trim()) params.search = search.trim();
            const res = await axios.get(`${API_BASE_URL}/dashboard-api/partners`, {
                params,
                headers: { Authorization: `Bearer ${localStorage.getItem("easybali_token")}` }
            });
            setApplications(res.data.applications || []);
            setCounts(res.data.counts || {});
        } catch {
            setApplications([]);
        } finally {
            setLoading(false);
        }
    }, [statusFilter, search]);

    useEffect(() => { fetchApplications(); }, [fetchApplications]);

    const handleDelete = async (app) => {
        if (!window.confirm(`Delete application from ${app.villa_name}? This cannot be undone.`)) return;
        setDeleting(app.application_id);
        try {
            await axios.delete(`${API_BASE_URL}/dashboard-api/partners/${app.application_id}`, {
                headers: { Authorization: `Bearer ${localStorage.getItem("easybali_token")}` }
            });
            fetchApplications();
        } catch {
            alert("Failed to delete");
        } finally {
            setDeleting(null);
        }
    };

    const handleQuickStatus = async (app, status) => {
        try {
            await axios.put(
                `${API_BASE_URL}/dashboard-api/partners/${app.application_id}/status`,
                { status },
                { headers: { Authorization: `Bearer ${localStorage.getItem("easybali_token")}` } }
            );
            fetchApplications();
        } catch {
            alert("Failed to update status");
        }
    };

    const TABS = [
        { key: "all", label: "All" },
        { key: "pending_review", label: "Pending" },
        { key: "accepted", label: "Accepted" },
        { key: "denied", label: "Denied" },
    ];

    return (
        <div className="flex flex-col gap-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-[#FF8000] to-orange-400 bg-clip-text text-transparent">
                        Villa Partnership Applications
                    </h1>
                    <p className="text-xs font-bold text-lightneutral mt-0.5 uppercase tracking-widest">Review, approve & manage partner applications</p>
                </div>
                <button
                    onClick={fetchApplications}
                    className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 text-gray-600 rounded-xl text-sm font-semibold hover:bg-gray-50 transition-colors self-start"
                >
                    <FiRefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
                </button>
            </div>

            {/* Stat cards */}
            <div className="flex flex-wrap gap-3">
                <StatCard label="Total" value={counts.all} color="border-gray-100" />
                <StatCard label="Pending" value={counts.pending_review} color="border-yellow-100" />
                <StatCard label="Accepted" value={counts.accepted} color="border-green-100" />
                <StatCard label="Denied" value={counts.denied} color="border-red-100" />
            </div>

            {/* Filters */}
            <div className="bg-white rounded-2xl border border-gray-100 p-4 flex flex-col sm:flex-row gap-3">
                <div className="flex gap-1.5 flex-wrap">
                    {TABS.map((tab) => (
                        <button
                            key={tab.key}
                            onClick={() => setStatusFilter(tab.key)}
                            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                                statusFilter === tab.key
                                    ? "bg-primary text-white shadow-blue-shadow"
                                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                            }`}
                        >
                            {tab.label} {counts[tab.key] !== undefined && tab.key !== "all" ? `(${counts[tab.key]})` : ""}
                        </button>
                    ))}
                </div>
                <div className="relative flex-1 min-w-[200px]">
                    <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
                    <input
                        type="text"
                        placeholder="Search villa, contact, area..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="w-full pl-8 pr-4 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-primary"
                    />
                </div>
            </div>

            {/* List */}
            {loading ? (
                <div className="flex justify-center items-center py-20">
                    <div className="w-8 h-8 border-2 border-primary/20 border-t-primary rounded-full animate-spin" />
                </div>
            ) : applications.length === 0 ? (
                <div className="bg-white rounded-2xl border border-gray-100 py-16 text-center">
                    <p className="text-gray-400 font-medium">No applications found.</p>
                </div>
            ) : (
                <div className="flex flex-col gap-3">
                    {applications.map((app) => (
                        <div key={app.id} className="bg-white rounded-2xl border border-gray-100 px-5 py-4 hover:border-gray-200 hover:shadow-sm transition-all">
                            <div className="flex flex-col sm:flex-row sm:items-start gap-4">
                                {/* Main info */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 flex-wrap">
                                        <h3 className="font-bold text-gray-900 text-base">{app.villa_name}</h3>
                                        <StatusBadge status={app.status} />
                                        <span className="text-xs text-gray-400 font-mono">{app.application_id}</span>
                                    </div>
                                    <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-sm text-gray-600">
                                        {app.area && (
                                            <span className="flex items-center gap-1">
                                                <FiMapPin size={12} className="text-gray-400" />{app.area}
                                            </span>
                                        )}
                                        {app.property_type && (
                                            <span className="flex items-center gap-1">
                                                <FiHome size={12} className="text-gray-400" />{app.property_type}
                                                {app.num_rooms && `, ${app.num_rooms} rooms`}
                                            </span>
                                        )}
                                        {app.max_guests && (
                                            <span className="flex items-center gap-1">
                                                <FiUsers size={12} className="text-gray-400" />Max {app.max_guests} guests
                                            </span>
                                        )}
                                        {(app.rate_min || app.rate_max) && (
                                            <span className="flex items-center gap-1">
                                                <FiDollarSign size={12} className="text-gray-400" />
                                                IDR {Number(app.rate_min || 0).toLocaleString()} – {Number(app.rate_max || 0).toLocaleString()}
                                            </span>
                                        )}
                                    </div>
                                    <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1.5 text-sm text-gray-500">
                                        {app.contact_name && (
                                            <span className="flex items-center gap-1">
                                                <FiUser size={12} className="text-gray-400" />
                                                {app.contact_name}{app.contact_role ? ` · ${app.contact_role}` : ""}
                                            </span>
                                        )}
                                        {app.contact_phone && (
                                            <span className="flex items-center gap-1">
                                                <FiPhone size={12} className="text-gray-400" />{app.contact_phone}
                                            </span>
                                        )}
                                        {app.contact_email && (
                                            <span className="flex items-center gap-1">
                                                <FiMail size={12} className="text-gray-400" />{app.contact_email}
                                            </span>
                                        )}
                                    </div>
                                    {app.submitted_at && (
                                        <p className="text-xs text-gray-400 mt-1.5">
                                            Submitted {new Date(app.submitted_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
                                            {app.reviewed_by && ` · Reviewed by ${app.reviewed_by}`}
                                        </p>
                                    )}
                                    {app.admin_note && (
                                        <p className="text-xs text-primary mt-1 italic">Note: {app.admin_note}</p>
                                    )}
                                </div>

                                {/* Action buttons */}
                                <div className="flex flex-row sm:flex-col gap-1.5 flex-shrink-0">
                                    <button
                                        onClick={() => setViewApp(app)}
                                        className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 text-gray-700 rounded-xl text-xs font-semibold hover:bg-gray-200 transition-colors"
                                    >
                                        <FiEye size={12} /> View
                                    </button>
                                    <button
                                        onClick={() => setEditApp(app)}
                                        className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/10 text-primary rounded-xl text-xs font-semibold hover:bg-primary/20 transition-colors"
                                    >
                                        <FiEdit2 size={12} /> Edit
                                    </button>
                                    {app.status === "pending_review" && (
                                        <button
                                            onClick={() => handleQuickStatus(app, "accepted")}
                                            className="flex items-center gap-1.5 px-3 py-1.5 bg-green-100 text-green-700 rounded-xl text-xs font-semibold hover:bg-green-200 transition-colors"
                                        >
                                            <FiCheck size={12} /> Accept
                                        </button>
                                    )}
                                    {app.status === "pending_review" && (
                                        <button
                                            onClick={() => handleQuickStatus(app, "denied")}
                                            className="flex items-center gap-1.5 px-3 py-1.5 bg-red-100 text-red-700 rounded-xl text-xs font-semibold hover:bg-red-200 transition-colors"
                                        >
                                            <FiX size={12} /> Deny
                                        </button>
                                    )}
                                    {app.contact_phone && (
                                        <a
                                            href={`https://wa.me/${app.contact_phone.replace(/\D/g, "")}`}
                                            target="_blank"
                                            rel="noreferrer"
                                            className="flex items-center gap-1.5 px-3 py-1.5 bg-green-100 text-green-700 rounded-xl text-xs font-semibold hover:bg-green-200 transition-colors"
                                        >
                                            <FiMessageSquare size={12} /> WA
                                        </a>
                                    )}
                                    <button
                                        onClick={() => handleDelete(app)}
                                        disabled={deleting === app.application_id}
                                        className="flex items-center gap-1.5 px-3 py-1.5 bg-red-50 text-red-500 rounded-xl text-xs font-semibold hover:bg-red-100 transition-colors disabled:opacity-50"
                                    >
                                        <FiTrash2 size={12} /> {deleting === app.application_id ? "..." : "Delete"}
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {viewApp && (
                <DetailModal
                    app={viewApp}
                    onClose={() => setViewApp(null)}
                    onStatusChange={fetchApplications}
                    onEdit={(a) => setEditApp(a)}
                />
            )}
            {editApp && (
                <EditModal
                    app={editApp}
                    onClose={() => setEditApp(null)}
                    onSaved={fetchApplications}
                />
            )}
        </div>
    );
}
