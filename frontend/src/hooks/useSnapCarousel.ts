import { useEffect, useRef, useState, type MouseEvent, type PointerEvent } from "react";

// The cards in view, numbered from 1, and whether the scroller is at either end
export type CarouselView = { first: number; last: number; atStart: boolean; atEnd: boolean };

// A mouse press only becomes a drag after this many pixels, so a click on a button still works
const DRAG_THRESHOLD_PX = 5;

// Smooth scrolling, unless the candidate asks for reduced motion
export function scrollBehaviour(): ScrollBehavior {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
}

// One card's width plus the gap after it. Each card is an [data-carousel-item] inside the scroller's list.
function measure(scroller: HTMLElement) {
  const list = scroller.querySelector("ol");
  const item = scroller.querySelector<HTMLElement>("[data-carousel-item]");
  if (!list || !item) return null;
  const gap = parseFloat(getComputedStyle(list).columnGap) || 0;
  return { step: item.offsetWidth + gap, gap };
}

function readView(scroller: HTMLElement, count: number): CarouselView | null {
  const size = measure(scroller);
  if (!size || size.step <= 0) return null;
  const maxScroll = scroller.scrollWidth - scroller.clientWidth;
  const atStart = scroller.scrollLeft <= 1;
  const atEnd = scroller.scrollLeft >= maxScroll - 1;
  const visible = Math.max(1, Math.floor((scroller.clientWidth + size.gap + 1) / size.step));
  if (atEnd) return { first: Math.max(1, count - visible + 1), last: count, atStart, atEnd };
  const first = Math.min(count, Math.round(scroller.scrollLeft / size.step) + 1);
  return { first, last: Math.min(count, first + visible - 1), atStart, atEnd };
}

function sameView(a: CarouselView, b: CarouselView) {
  return a.first === b.first && a.last === b.last && a.atStart === b.atStart && a.atEnd === b.atEnd;
}

type Drag = { pointerId: number; startX: number; startScroll: number; moved: boolean };

// A horizontal scroll-snap list of cards: which cards are in view (for the counter and the arrows), one-card
// scrolling for the arrows, and mouse dragging. Touch and trackpads scroll it natively, and the arrow keys scroll it
// when it has focus.
export function useSnapCarousel(count: number) {
  const scrollerRef = useRef<HTMLDivElement>(null);
  // A first guess for a wide page (3 across) until the first measurement, so the counter rarely changes on load
  const [view, setView] = useState<CarouselView>(() => ({
    first: 1,
    last: Math.min(count, 3),
    atStart: true,
    atEnd: count <= 3,
  }));
  const [dragging, setDragging] = useState(false);
  const dragRef = useRef<Drag | null>(null);
  // Set when a drag ends, so the click that ends it doesn't press the button under the pointer
  const suppressClickRef = useRef(false);

  useEffect(() => {
    const scroller = scrollerRef.current;
    if (!scroller) return;
    let frame = 0;

    function update() {
      frame = 0;
      if (!scroller) return;
      const next = readView(scroller, count);
      if (next) setView((current) => (sameView(current, next) ? current : next));
    }

    // At most one update per frame while scrolling
    function schedule() {
      if (!frame) frame = window.requestAnimationFrame(update);
    }

    schedule();
    scroller.addEventListener("scroll", schedule, { passive: true });
    const observer = new ResizeObserver(schedule);
    observer.observe(scroller);
    return () => {
      window.cancelAnimationFrame(frame);
      scroller.removeEventListener("scroll", schedule);
      observer.disconnect();
    };
  }, [count]);

  // Scrolls one card back (-1) or on (1). Scroll snapping lands it on the card's start.
  function scrollByCard(direction: -1 | 1) {
    const scroller = scrollerRef.current;
    const size = scroller && measure(scroller);
    if (!scroller || !size) return;
    scroller.scrollBy({ left: direction * size.step, behavior: scrollBehaviour() });
  }

  function onPointerDown(event: PointerEvent<HTMLDivElement>) {
    suppressClickRef.current = false;
    if (event.pointerType !== "mouse" || event.button !== 0) return;
    dragRef.current = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startScroll: event.currentTarget.scrollLeft,
      moved: false,
    };
  }

  function onPointerMove(event: PointerEvent<HTMLDivElement>) {
    const drag = dragRef.current;
    if (!drag || event.pointerId !== drag.pointerId) return;
    const dx = event.clientX - drag.startX;
    if (!drag.moved) {
      if (Math.abs(dx) < DRAG_THRESHOLD_PX) return;
      drag.moved = true;
      event.currentTarget.setPointerCapture(event.pointerId);
      // Text selected in the first few pixels would otherwise stay highlighted
      window.getSelection()?.removeAllRanges();
      setDragging(true);
    }
    event.currentTarget.scrollLeft = drag.startScroll - dx;
  }

  function endDrag(event: PointerEvent<HTMLDivElement>) {
    const drag = dragRef.current;
    if (!drag || event.pointerId !== drag.pointerId) return;
    dragRef.current = null;
    if (!drag.moved) return;

    const scroller = event.currentTarget;
    suppressClickRef.current = true;
    // The click (if any) follows straight after pointerup, so a later keyboard click isn't swallowed
    window.setTimeout(() => {
      suppressClickRef.current = false;
    }, 0);
    setDragging(false);
    // Snapping is back on after this render: settle on the nearest card
    window.requestAnimationFrame(() => {
      const size = measure(scroller);
      if (!size) return;
      scroller.scrollTo({ left: Math.round(scroller.scrollLeft / size.step) * size.step, behavior: scrollBehaviour() });
    });
  }

  function onClickCapture(event: MouseEvent<HTMLDivElement>) {
    if (!suppressClickRef.current) return;
    suppressClickRef.current = false;
    event.preventDefault();
    event.stopPropagation();
  }

  return {
    scrollerRef,
    view,
    dragging,
    scrollByCard,
    scrollerProps: {
      onPointerDown,
      onPointerMove,
      onPointerUp: endDrag,
      onPointerCancel: endDrag,
      onClickCapture,
    },
  };
}
