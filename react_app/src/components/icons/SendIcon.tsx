export default function SendIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.3"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {/* Left → right → rounded turn → up */}
      <path d="M3 16h10a4 4 0 0 0 4-4V6" />

      {/* Arrowhead pointing up */}
      <path d="M13 9l4-4 4 4" />
    </svg>
  );
}
