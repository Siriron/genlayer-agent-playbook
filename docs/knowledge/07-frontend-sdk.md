## 7. Frontend SDK (confirmed working)

- Chain imports from `genlayer-js/chains`, not `genlayer-js` directly.
- Correct export: `studionet`.
- Reads: `createClient({chain: studionet})`.
- Writes: `createClient({chain, account, provider: window.ethereum})`. Passing `provider: window.ethereum` is required — confirmed via a real accepted, deployed working code (`useGenLayer.js`/`useGenLayer.ts`), which explicitly sets this field. Omitting it caused a confirmed live bug where transactions filed silently executed on the wrong network, because the wallet was never told to switch chains and the client had no wallet provider bound to force it.
- **`account` must be the connected wallet's plain address string, never wrapped in `createAccount()` (confirmed live bug, Aug 2026).** `createAccount()` expects a **private key**, not a wallet address — confirmed directly against GenLayer's own SDK documentation, in their own words: "Use `createAccount()` when you want the SDK to handle transaction signing directly. For MetaMask or other external wallet integration, pass just the address string to `createClient()`." A wallet address and a private key are both `0x`-prefixed hex strings, so passing the wrong one into `createAccount()` does not throw a type error — it silently produces a broken or mismatched signing setup that can fail unpredictably on real write transactions in production, a materially worse failure mode than a compile-time error since it can pass casual testing. For any browser-wallet-connected app (the standard pattern here: `window.ethereum`, `eth_requestAccounts`, no private key ever touches the app), pass `account: connectedAddress as \`0x${string}\`` directly — never `createAccount(connectedAddress)`.
- Never rely on the `genlayer-js` client's internal chain config alone to put the wallet on the right network. Call an explicit `ensureChain()` step before every write. Confirmed working pattern:
```javascript
const STUDIONET_CONFIG = {
  chainId: '0xF22F', // 61999
  chainName: 'GenLayer StudioNet',
  rpcUrls: ['https://studio.genlayer.com/api'],
  nativeCurrency: { name: 'GEN', symbol: 'GEN', decimals: 18 },
  blockExplorerUrls: ['https://explorer-studio.genlayer.com'],
};

async function ensureChain() {
  const eth = window.ethereum;
  if (!eth) return;
  try {
    await eth.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: STUDIONET_CONFIG.chainId }] });
  } catch (err) {
    if (err && err.code === 4902) {
      await eth.request({ method: 'wallet_addEthereumChain', params: [STUDIONET_CONFIG] });
      await eth.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: STUDIONET_CONFIG.chainId }] });
    } else if (err && err.code === -32002) {
      await new Promise((r) => setTimeout(r, 3000));
    } else {
      throw err;
    }
  }
}
```
Call `ensureChain()` immediately before every write.

- After creating the write client, also defensively try `await client.connect('studionet')` if the method exists (`typeof client.connect === 'function'`). This isn't shown in any official SDK example but is present in real working code; guard it defensively so contracts built on SDK versions without it don't throw.
- Wallet connection must persist and stay in sync, not just connect once on button click. Confirmed pattern:
```javascript
useEffect(() => {
  const eth = window.ethereum;
  if (!eth) return;
  eth.request({ method: 'eth_accounts' }).then((accounts) => {
    if (accounts[0]) setAccount(accounts[0]);
  }).catch(() => {});
  const handleAccountsChanged = (accounts) => setAccount(accounts[0] || null);
  if (eth.on) eth.on('accountsChanged', handleAccountsChanged);
  return () => { if (eth.removeListener) eth.removeListener('accountsChanged', handleAccountsChanged); };
}, []);
```
On mount, silently check `eth_accounts` (not `eth_requestAccounts`, which would prompt) to reconnect without a click if already authorized, and subscribe to `accountsChanged` to stay in sync if the person switches wallets.
- `writeContract` requires `value: BigInt(0)` even when unused.
- `readContract` returns a JSON string — always parse it.
- `TransactionStatus` from `genlayer-js/types`; wait with `status: TransactionStatus.ACCEPTED`.
- `waitForTransactionReceipt` needs generous retry/interval config — the SDK default is too short. GenLayer consensus genuinely takes real minutes, not seconds, especially for any write that triggers an LLM judgment. Confirmed reasonable values: `{ retries: 120, interval: 4000 }`.
If it still times out, don't just show a bare error — surface a direct explorer link to the actual transaction, since the transaction may have genuinely succeeded even though the frontend gave up waiting. Show a "this can take several minutes" note under any pending write button.

**Confirmed implementation pattern for the above:** build a real `Error` object/class carrying the tx hash and a timeout flag as real properties, not just a string message:
```javascript
class TimeoutError extends Error {
  txHash: string;
  isTimeout = true;
  constructor(hash: string) {
    super(`Consensus is taking longer than expected. Your transaction was submitted — check its status directly: ${EXPLORER_TX_URL(hash)}`);
    this.txHash = hash;
  }
}
```
Throw this specific error from the catch branch of every `waitForTransactionReceipt` call, and have the UI check for it distinctly from a generic failure — a timeout is not the same UI state as a rejected transaction.
- Confirmed working `genlayer-js` subpaths: `genlayer-js` (root), `genlayer-js/chains`, `genlayer-js/types`. There is no `genlayer-js/utils` subpath — it does not exist and breaks the Vite/Vercel build with `[commonjs--resolver] Missing "./utils" specifier`. `genlayer-js` is built on top of Viem but does not re-export Viem's utilities under its own path. For any Viem-shaped helper (`parseEther`, `formatEther`, `parseUnits`), import directly from `viem` and add `viem` as an explicit `package.json` dependency. Never import from a `genlayer-js/*` subpath not in this confirmed list without verifying it first.
- React + Vite is accepted (not just Next.js). `index.html` must be in project root, not `public/`.
- `vercel.json` needs SPA rewrite: `{"rewrites":[{"source":"/(.*)", "destination":"/index.html"}]}`.
- `genlayer-js` version `^1.1.7` confirmed working.
- **Contract address: a single plain constant in `/src/config/chains.ts`, no `.env`/`.env.example`/`.gitignore`, no Vercel environment variable.** Confirmed working and confirmed strongly preferred going forward: `export const CONTRACT_ADDRESS = '0x...'` as a plain literal, referenced from nowhere else in the app. Changing the deployed address — which happens often in this project's own redeploy cycle — means editing one line in one file, no dashboard, no dotfiles invisible on mobile file browsers, no environment-variable indirection to keep in sync. This is a deliberate reversal of this document's own prior guidance (which favored `VITE_CONTRACT_ADDRESS_*` env vars with an `.env`/`.env.example` pair) — that pattern still works and isn't wrong, but the plain-constant pattern is simpler, has zero moving parts to keep in sync, and is the confirmed standing choice for every app in this project going forward.
- Never reference `import.meta.env.VITE_*` for the contract address if following the plain-constant pattern above — that indirection implies a configurability that isn't being used, and a stray `||` fallback to a hardcoded value is functionally identical to the constant but reads as more configurable than it is.

**Network config:**
| | StudioNet |
|---|---|
| RPC | https://studio.genlayer.com/api |
| Chain ID | 61999 (0xF22F) |
| Explorer | explorer-studio.genlayer.com |

This project targets StudioNet exclusively. No network toggle, no Bradbury wiring, no dual-network `ensureChain`/`RECEIPT_CONFIG` branching — a network toggle with only one real network behind it is worse than no toggle at all.
