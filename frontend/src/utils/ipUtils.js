// CIDR u IP Kalkulator
export function calculateIPs(cidr) {
  try {
    const [ip, mask] = cidr.split('/');
    if (!ip || !mask) return null;

    const ipParts = ip.split('.').map(Number);
    if (ipParts.length !== 4) return null;

    // Konverzija u 32-bitni ceo broj
    let ipInt = (ipParts[0] << 24) | (ipParts[1] << 16) | (ipParts[2] << 8) | ipParts[3];
    // Konverzija u unsigned
    ipInt = ipInt >>> 0;

    // Kreiranje maske
    const maskBits = parseInt(mask, 10);
    const maskInt = (-1 << (32 - maskBits)) >>> 0;
    
    // Mrežna Adresa
    const networkInt = (ipInt & maskInt) >>> 0;

    // Prvi Host
    const firstHostInt = (networkInt + 1) >>> 0;
    // Drugi Host
    const secondHostInt = (networkInt + 2) >>> 0;

    const intToIp = (int) => {
      return [
        (int >>> 24) & 0xFF,
        (int >>> 16) & 0xFF,
        (int >>> 8) & 0xFF,
        int & 0xFF
      ].join('.');
    };

    return {
      network: intToIp(networkInt),
      firstHost: intToIp(firstHostInt),
      secondHost: intToIp(secondHostInt),
      mask: maskBits
    };
  } catch (e) {
    console.error("Invalid CIDR", e);
    return null;
  }
}
