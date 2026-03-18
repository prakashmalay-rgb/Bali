import React, { useState } from "react";
import Hero from "../components/home/hero";
import Services from "../components/home/services";
import Experience from "../components/home/experience";
import TryUs from "../components/home/tryUs";
import VillaPartnershipForm from "../components/home/VillaPartnershipForm";
import Footer from "../components/layout/footer";

const Home = () => {
  const [showPartnershipForm, setShowPartnershipForm] = useState(false);

  return (
    <>
      <div className="relative flex flex-col justify-center items-center mx-3 sm:mx-5 mt-5">
        <Hero />
        <div className="container px-[18px] lg:px-[40px] flex flex-col relative mt-20 gap-16 pb-16">
          <Services />
          <Experience />
          <TryUs />

          {/* Villa Partnership CTA */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6 rounded-[30px] sm:rounded-[40px] bg-[#FFF5EB] border border-[#FFD6A0] px-8 sm:px-12 py-8 sm:py-10">
            <div className="flex flex-col gap-2 text-center sm:text-left">
              <h3 className="text-[20px] sm:text-[24px] font-bold text-gray-900">Own a Villa in Bali?</h3>
              <p className="text-gray-600 text-[14px] sm:text-[16px] max-w-[420px]">
                Partner with EasyBali to offer your guests seamless concierge services and grow your villa's revenue.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowPartnershipForm(true)}
              className="flex-shrink-0 px-8 py-4 rounded-[50px] bg-[#FF8000] text-white font-bold text-[15px] hover:bg-[#e67200] transition-colors shadow-orange-shadow"
            >
              Become a Partner
            </button>
          </div>
        </div>
        <img
          src="/images/star1.png"
          alt="img"
          className="absolute top-[15%] sm:top-[-1%] -z-10 left-[-7%] max-w-[237px] sm:max-w-[709px] w-full "
        />
        <img
          src="/images/star2.png"
          alt="img"
          className="absolute bottom-[11%] sm:bottom-[14%] -z-10 right-[-11px] max-width-[324px] sm:max-size-[709px]"
        />
        <img
          src="/images/star3.png"
          alt="img"
          className="absolute bottom-[-5%] -z-10 left-[-20px] max-size-[709px]"
        />
      </div>
      <Footer />
      {showPartnershipForm && (
        <VillaPartnershipForm onClose={() => setShowPartnershipForm(false)} />
      )}
    </>
  );
};

export default Home;
