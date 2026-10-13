// Screen registry. Each screen module exports `render(container, params): void | Promise<void>` and may export `unmount()`.
// UI agents replace the placeholders below with real screens in their own files.
export interface Screen {
  render(container: HTMLElement, params: string[]): void | Promise<void>;
  unmount?(): void;
}
