import { useEffect } from "react";
export default function OAuthSuccess() {
  useEffect(() => {
    window.location.replace("/home");
  }, []);

  return (
    <div className="loading-screen">
      <span className="spinner spinner--dark" />
    </div>
  );
}
