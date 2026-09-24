import LectureWorkspacePage from "./workspace";

export const dynamic = "force-static";
export const dynamicParams = false;

export async function generateStaticParams() {
  return [{ jobId: "DEMO_python_loops" }, { jobId: "DEMO_python_loops.mp4" }];
}

export default async function LectureWorkspacePageRoute({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const { jobId } = await params;
  return <LectureWorkspacePage jobId={jobId} />;
}