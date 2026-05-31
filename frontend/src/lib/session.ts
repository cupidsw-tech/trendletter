import { getServerSession } from "next-auth";
import { authOptions } from "./auth";

export async function getSessionUser() {
  const session = await getServerSession(authOptions);
  if (!session?.user) return null;
  return { id: (session.user as any).id as string, email: session.user.email! };
}
