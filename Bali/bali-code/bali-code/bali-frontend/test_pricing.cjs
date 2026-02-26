const axios = require('axios');

async function testLocations() {
    const baseUrl = "https://bali-v92r.onrender.com/menu/price_distribution"; // Or window.location / localhost
    const service = "Basic Deep Cleaning/hour";

    // As per the User: "Zone 1", "Zone 2", "Ubud", "Canggu", "Seminyak"
    const zones = ["Zone 1", "Zone 2", "Ubud", "Canggu", "Seminyak"];

    for (const zone of zones) {
        console.log(`\n--- Testing Zone: ${zone} ---`);
        try {
            const response = await axios.get(baseUrl, {
                params: { service_item: service, location_zone: zone }
            });
            console.log(`Service: ${response.data.service_item}`);
            console.log(`Vendor Price: ${response.data.service_provider_price}`);
            console.log(`Villa Comm (Applied Rate): ${response.data.villa_price}`);
            console.log(`Applied Zone Strategy: ${response.data.applied_zone}`);
        } catch (error) {
            console.log(`Error: ${error.response ? error.response.status : error.message}`);
        }
    }
}

testLocations();
