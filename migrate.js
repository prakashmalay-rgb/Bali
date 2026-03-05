const { MongoClient } = require('mongodb');

async function migrateDatabase() {
    const sourceUri = "mongodb+srv://4772hassan:txI6i6DkVVHA3GGl@easybalicluster.qcpk7.mongodb.net/";
    const destUri = "mongodb+srv://prakashmalay_db_user:QbBqlWv1K676Y9V4@easybali.xvindoa.mongodb.net/";

    const sourceClient = new MongoClient(sourceUri);
    const destClient = new MongoClient(destUri);

    try {
        console.log("Connecting to both databases...");
        await sourceClient.connect();
        await destClient.connect();
        console.log("Connected successfully.\n");

        const sourceDb = sourceClient.db('easybali');
        const destDb = destClient.db('easybali');

        // Get all collections from the source database
        const collections = await sourceDb.listCollections().toArray();
        console.log(`Found ${collections.length} collections to migrate.`);

        for (const colInfo of collections) {
            const collectionName = colInfo.name;
            console.log(`\nStarting migration for collection: ${collectionName}`);

            const sourceCollection = sourceDb.collection(collectionName);
            const destCollection = destDb.collection(collectionName);

            // Fetch all documents from the source collection
            const documents = await sourceCollection.find({}).toArray();

            if (documents.length > 0) {
                // Wipe the destination collection to prevent duplicate key errors if this runs twice
                await destCollection.deleteMany({});

                // Insert the copied documents
                await destCollection.insertMany(documents);
                console.log(` ✅ Successfully transferred ${documents.length} documents into ${collectionName}`);
            } else {
                console.log(` ➖ Collection ${collectionName} was empty. Skipped.`);
            }
        }

        console.log("\nDATABASE SECURELY MIGRATED!");

    } catch (error) {
        console.error("Error migrating database:", error);
    } finally {
        await sourceClient.close();
        await destClient.close();
    }
}

migrateDatabase();
