const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

async function main() {
  const users = await prisma.user.findMany();
  if (users.length === 0) {
    console.log("No users found in the database. Please sign in with Google first.");
    return;
  }
  
  console.log("Found users:");
  for (const user of users) {
    console.log(`- ${user.email} (isAdmin: ${user.isAdmin})`);
    
    // Elevate all current users to admin for testing purposes
    await prisma.user.update({
      where: { id: user.id },
      data: { isAdmin: true }
    });
    console.log(`✅ Elevated ${user.email} to Admin!`);
  }
}

main()
  .catch(e => console.error(e))
  .finally(async () => await prisma.$disconnect());
