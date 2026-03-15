import { useState, useEffect, useCallback } from 'react';
import {
    FiSearch, FiFilter, FiCalendar, FiCheckCircle, FiClock, FiXCircle,
    FiX, FiUser, FiMapPin, FiCreditCard, FiTool, FiExternalLink
} from 'react-icons/fi';
import { API_BASE_URL, apiRequest } from '../../api/apiClient';
import axios from 'axios';

const formatIDR = (num) => {
    if (!num && num !== 0) return '—';
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(num);
};

const STATUS_STYLES = {
    PAID: 'bg-emerald-50 text-emerald-600 border-emerald-100',
    PENDING: 'bg-orange-50 text-orange-600 border-orange-100',
    CANCELLED: 'bg-rose-50 text-rose-600 border-rose-100',
};

const StatusBadge = ({ status }) => (
    <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase border inline-flex items-center gap-1.5 ${STATUS_STYLES[status] || 'bg-blue-50 text-primary border-blue-100'}`}>
        {status === 'PAID' && <FiCheckCircle />}
        {status === 'PENDING' && <FiClock />}
        {status === 'CANCELLED' && <FiXCircle />}
        {status}
    </span>
);

const InvoiceDownloadButton = ({ orderNumber }) => {
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState('');

    const handleClick = async () => {
        setLoading(true);
        setErr('');
        try {
            const res = await apiRequest(() =>
                axios.get(`${API_BASE_URL}/dashboard-api/bookings/${orderNumber}/invoice-url`)
            );
            if (res.data.success) {
                window.open(res.data.url, '_blank', 'noopener,noreferrer');
            } else {
                setErr(res.data.error || 'Failed to get invoice URL');
            }
        } catch {
            setErr('Could not load invoice');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <button
                onClick={handleClick}
                disabled={loading}
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white text-xs font-black rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50"
            >
                {loading ? 'Loading...' : <><FiExternalLink size={11} /> Download Invoice PDF</>}
            </button>
            {err && <p className="text-xs text-rose-500 mt-1">{err}</p>}
        </div>
    );
};

const DetailRow = ({ label, value }) => (
    <div className="flex justify-between items-start gap-4 py-2 border-b border-gray-50 last:border-0">
        <span className="text-[11px] font-black uppercase tracking-widest text-lightneutral whitespace-nowrap">{label}</span>
        <span className="text-sm font-bold text-neutral text-right break-all">{value || '—'}</span>
    </div>
);

const Section = ({ icon: Icon, title, children }) => (
    <div className="bg-gray-50/60 rounded-2xl p-4 space-y-1">
        <div className="flex items-center gap-2 mb-3">
            <div className="p-1.5 rounded-lg bg-primary/10 text-primary"><Icon size={13} /></div>
            <h3 className="text-[11px] font-black uppercase tracking-widest text-lightneutral">{title}</h3>
        </div>
        {children}
    </div>
);

const BookingDetailDrawer = ({ bookingRef, onClose }) => {
    const [detail, setDetail] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!bookingRef) return;
        setLoading(true);
        apiRequest(() => axios.get(`${API_BASE_URL}/dashboard-api/bookings/${bookingRef}`))
            .then(res => { if (res.data.success) setDetail(res.data.booking); })
            .catch(() => {})
            .finally(() => setLoading(false));
    }, [bookingRef]);

    return (
        <div className="fixed inset-0 z-50 flex justify-end" onClick={onClose}>
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/20 backdrop-blur-sm" />

            {/* Drawer */}
            <div
                className="relative w-full max-w-lg h-full bg-white shadow-2xl overflow-y-auto flex flex-col"
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-5 border-b border-gray-100 sticky top-0 bg-white z-10">
                    <div>
                        <p className="text-xs font-black uppercase tracking-widest text-lightneutral">Booking Detail</p>
                        <h2 className="text-xl font-black text-neutral">{bookingRef}</h2>
                    </div>
                    <button onClick={onClose} className="p-2 rounded-xl hover:bg-gray-100 transition-colors text-lightneutral hover:text-neutral">
                        <FiX size={18} />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 px-6 py-5 space-y-4">
                    {loading ? (
                        <div className="flex items-center justify-center py-20 text-sm font-bold text-lightneutral italic">Loading...</div>
                    ) : !detail ? (
                        <div className="flex items-center justify-center py-20 text-sm font-bold text-rose-400">Could not load booking details.</div>
                    ) : (
                        <>
                            {/* Status + timestamps */}
                            <div className="flex items-center justify-between">
                                <StatusBadge status={detail.status} />
                                <span className="text-[11px] font-bold text-lightneutral">{detail.created_at ? new Date(detail.created_at).toLocaleString('en-GB') : '—'}</span>
                            </div>

                            {/* Service */}
                            <Section icon={FiCalendar} title="Service">
                                <DetailRow label="Service" value={detail.service_name} />
                                <DetailRow label="Date" value={detail.date ? new Date(detail.date).toLocaleDateString('en-GB') : null} />
                                <DetailRow label="Time" value={detail.time} />
                                <DetailRow label="Price" value={detail.price} />
                                {detail.promo_code && <DetailRow label="Promo Code" value={detail.promo_code} />}
                                {detail.discount_amount ? <DetailRow label="Discount" value={formatIDR(detail.discount_amount)} /> : null}
                                {detail.original_price && <DetailRow label="Original Price" value={detail.original_price} />}
                            </Section>

                            {/* Guest & Villa */}
                            <Section icon={FiUser} title="Guest & Villa">
                                <DetailRow label="Guest ID" value={detail.sender_id} />
                                <DetailRow label="Villa" value={detail.villa_code} />
                            </Section>

                            {/* Service Provider */}
                            <Section icon={FiTool} title="Service Provider">
                                <DetailRow label="Assigned SP" value={detail.service_provider_code || detail.assigned_provider} />
                                <DetailRow label="Confirmed By" value={detail.confirmed_by_provider} />
                                <DetailRow label="Confirmed At" value={detail.confirmed_at ? new Date(detail.confirmed_at).toLocaleString('en-GB') : null} />
                            </Section>

                            {/* Payment */}
                            <Section icon={FiCreditCard} title="Payment">
                                <DetailRow label="Amount Paid" value={formatIDR(detail.payment?.paid_amount)} />
                                <DetailRow label="Method" value={detail.payment?.payment_method} />
                                <DetailRow label="Paid At" value={detail.payment?.paid_at ? new Date(detail.payment.paid_at).toLocaleString('en-GB') : null} />
                                <DetailRow label="Status" value={detail.payment?.payment_status} />
                                <DetailRow label="Xendit Invoice ID" value={detail.payment?.xendit_invoice_id} />
                                {detail.payment?.payment_url && (
                                    <div className="flex justify-between items-center py-2">
                                        <span className="text-[11px] font-black uppercase tracking-widest text-lightneutral">Payment Link</span>
                                        <a href={detail.payment.payment_url} target="_blank" rel="noopener noreferrer"
                                            className="text-primary text-sm font-bold flex items-center gap-1 hover:underline">
                                            Open <FiExternalLink size={11} />
                                        </a>
                                    </div>
                                )}
                            </Section>

                            {/* Payment Split */}
                            {detail.payment?.distribution_data && (
                                <Section icon={FiMapPin} title="Payment Split">
                                    <DetailRow label="SP Share" value={formatIDR(detail.payment.distribution_data.sp_share)} />
                                    <DetailRow label="Villa Share" value={formatIDR(detail.payment.distribution_data.villa_share)} />
                                    <DetailRow label="EasyBali Share" value={formatIDR(detail.payment.distribution_data.eb_share)} />
                                </Section>
                            )}

                            {/* Invoice */}
                            {(detail.invoice?.download_url || detail.invoice?.object_key) && (
                                <Section icon={FiExternalLink} title="Invoice">
                                    <div className="pt-1">
                                        <InvoiceDownloadButton orderNumber={detail.order_number} />
                                    </div>
                                </Section>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

const BookingsView = () => {
    const [bookings, setBookings] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterStatus, setFilterStatus] = useState('ALL');
    const [selectedBooking, setSelectedBooking] = useState(null);

    const fetchBookings = useCallback(async () => {
        setIsLoading(true);
        try {
            const params = new URLSearchParams();
            if (filterStatus !== 'ALL') params.set('status', filterStatus);
            if (searchTerm.trim()) params.set('search', searchTerm.trim());
            const url = `${API_BASE_URL}/dashboard-api/bookings?${params.toString()}`;
            const response = await apiRequest(() => axios.get(url));
            if (response.data.success) setBookings(response.data.bookings);
        } catch (error) {
            console.error('Failed to fetch bookings');
        } finally {
            setIsLoading(false);
        }
    }, [filterStatus, searchTerm]);

    // Debounce search
    useEffect(() => {
        const timer = setTimeout(fetchBookings, 400);
        return () => clearTimeout(timer);
    }, [fetchBookings]);

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-black text-neutral uppercase tracking-tight">Service <span className="text-primary">Bookings</span></h1>
                <p className="text-sm font-medium text-lightneutral mt-1">Manage all service requests and orders across villas.</p>
            </div>

            {/* Filters bar */}
            <div className="flex flex-col md:flex-row gap-4 bg-white/60 backdrop-blur-md p-4 rounded-[2rem] border border-white shadow-sm">
                <div className="flex-1 relative group">
                    <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-lightneutral group-focus-within:text-primary transition-colors" />
                    <input
                        type="text"
                        placeholder="Search by Order ID, Guest, or Service..."
                        className="w-full pl-12 pr-4 py-3 bg-white border border-gray-100 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-sm font-medium"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <div className="flex items-center gap-2">
                    <FiFilter className="text-lightneutral ml-2" />
                    <select
                        className="bg-white border border-gray-100 rounded-2xl px-4 py-3 text-sm font-bold text-neutral focus:outline-none focus:ring-2 focus:ring-primary/20"
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value)}
                    >
                        <option value="ALL">ALL STATUS</option>
                        <option value="PAID">PAID</option>
                        <option value="PENDING">PENDING</option>
                        <option value="CANCELLED">CANCELLED</option>
                    </select>
                </div>
            </div>

            {/* Table Container */}
            <div className="bg-white/70 backdrop-blur-xl border border-white rounded-[2.5rem] shadow-sm overflow-hidden text-sm">
                <div className="overflow-x-auto p-2">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="text-[10px] font-black text-lightneutral uppercase tracking-[0.2em] border-b border-gray-100/30">
                                <th className="px-6 py-5">Order Reference</th>
                                <th className="px-6 py-5">Guest</th>
                                <th className="px-6 py-5">Service</th>
                                <th className="px-6 py-5">Villa</th>
                                <th className="px-6 py-5">Amount</th>
                                <th className="px-6 py-5 text-right">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50/50">
                            {isLoading ? (
                                <tr><td colSpan="6" className="py-20 text-center font-bold text-lightneutral italic">Retrieving secure records...</td></tr>
                            ) : bookings.length === 0 ? (
                                <tr><td colSpan="6" className="py-20 text-center font-bold text-lightneutral italic">No matching bookings found.</td></tr>
                            ) : (
                                bookings.map((b) => (
                                    <tr
                                        key={b.id}
                                        onClick={() => setSelectedBooking(b.order_number)}
                                        className="hover:bg-white/80 transition-all cursor-pointer border-l-4 border-l-transparent hover:border-l-primary"
                                    >
                                        <td className="px-6 py-5">
                                            <div className="flex items-center gap-2">
                                                <div className="p-2 rounded-xl bg-primary/5 text-primary"><FiCalendar /></div>
                                                <div>
                                                    <p className="font-black text-neutral tracking-tight underline decoration-primary/20 decoration-2 underline-offset-4">{b.order_number}</p>
                                                    <p className="text-[9px] font-black text-lightneutral uppercase mt-0.5">{b.time}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-5 font-bold text-darkgrey uppercase tracking-tighter">
                                            {b.guest_id ? `...${b.guest_id.slice(-6)}` : 'UNKNOWN'}
                                        </td>
                                        <td className="px-6 py-5 font-black text-neutral">{b.service}</td>
                                        <td className="px-6 py-5 font-bold text-lightneutral tracking-widest">{b.villa}</td>
                                        <td className="px-6 py-5 font-black text-neutral">{formatIDR(b.amount)}</td>
                                        <td className="px-6 py-5 text-right">
                                            <StatusBadge status={b.status} />
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Detail Drawer */}
            {selectedBooking && (
                <BookingDetailDrawer
                    bookingRef={selectedBooking}
                    onClose={() => setSelectedBooking(null)}
                />
            )}
        </div>
    );
};

export default BookingsView;
