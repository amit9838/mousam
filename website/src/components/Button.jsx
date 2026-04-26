import React from 'react';

/**
 * Reusable button component for the website.
 *
 * Props:
 * - children: button label or inner content
 * - onClick: click handler (optional)
 * - href: if provided, renders an <a> element styled as a button
 * - variant: "primary" | "secondary" (default: "primary")
 * - size: "sm" | "md" | "lg" (default: "md")
 * - className: additional tailwind classes
 */
export default function Button({
  children,
  onClick,
  href,
  variant = 'primary',
  size = 'md',
  className = '',
  ...props
}) {
  const baseClasses = 'inline-flex items-center justify-center font-bold transition-colors duration-200 focus:outline-none';
  const variantClasses = {
    primary: 'bg-sky-600 hover:bg-sky-700 text-white shadow-xl shadow-sky-500/20 active:scale-95',
    secondary: 'bg-white/5 hover:bg-white/10 text-white border border-white/10 active:scale-95',
    white: 'bg-white hover:bg-neutral-200 text-black active:scale-95',
  }[variant];
  const sizeClasses = {
    sm: 'px-4 py-1.5 text-xs rounded-md',
    md: 'px-8 py-3 text-sm rounded-lg',
    lg: 'px-10 py-4 text-base rounded-xl',
    icon: 'w-10 h-10 rounded-full',
  }[size];

  const combined = `${baseClasses} ${variantClasses} ${sizeClasses} ${className}`.trim();

  if (href) {
    return (
      <a href={href} onClick={onClick} className={combined} {...props}>
        {children}
      </a>
    );
  }

  return (
    <button type="button" onClick={onClick} className={combined} {...props}>
      {children}
    </button>
  );
}
