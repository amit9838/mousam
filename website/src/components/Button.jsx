export default function Button({ children, myStyle, ...props }) {
  let styles = "hover:bg-primary px-4 py-2 text-sm";
  if (myStyle != null) {
    styles = styles+ " "+ myStyle;
  }

  return (
    <button className={styles} {...props}>
      {children}
    </button>
  );
}
