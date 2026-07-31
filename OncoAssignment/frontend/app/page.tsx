import { PresentationChat } from "./components/PresentationChat";
import { ALL_CASES, publicImagePath } from "@/lib/case-data";

export default function Home() {
  const cases = ALL_CASES.map((c) => ({
    ...c,
    images: c.images.map((img) => ({ ...img, src: publicImagePath(c.id, img) }))
  }));

  return <PresentationChat cases={cases} />;
}
