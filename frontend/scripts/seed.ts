const { PrismaClient } = require("@prisma/client");

const database = new PrismaClient();

async function main() {
  const categories = [
    { name: "Computer Science" },
    { name: "Computer Engineering" },
    { name: "Artificial Intelligence" }, // Corrected typo
    { name: "Web Development" },
    { name: "Cybersecurity" }, // Corrected typo
    { name: "Data Science" },
    { name: "Machine Learning" },
  ];

  try {
    for (const category of categories) {
      await database.category.upsert({
        where: { name: category.name },
        update: {},
        create: category,
      });
    }
    console.log("Database seeded successfully.");
  } catch (error) {
    console.log("Error seeding the database categories", error);
  } finally {
    await database.$disconnect();
  }
}

main();
