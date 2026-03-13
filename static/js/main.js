let errorsCount = 0;
let isDegraded = false;

async function handleOrder() {
    if (isDegraded) return; // Не даємо натискати, якщо режим деградації активний

    const btn = document.getElementById('order-button');
    const banner = document.getElementById('degraded-banner');

    try {
        // Викликаємо твій стійкий хелпер (який ми писали раніше)
        const res = await fetchWithResilience("/api/orders", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title: "Order Item" }),
            idempotencyKey: await getOrReuseKey({ title: "Order Item" }) // Ключ ідемпотентності
        });

        if (!res.ok) throw new Error("Server error");

        errorsCount = 0; // Скидаємо лічильник при успіху
        alert("Замовлення успішно створено!");

    } catch (e) {
        errorsCount++;
        console.log(`Помилка №${errorsCount}`);

        // Якщо 3 збої поспіль — вмикаємо Degraded Mode
        if (errorsCount >= 3) {
            isDegraded = true;
            btn.disabled = true; // Дизейблимо кнопку
            btn.innerText = "Заблоковано";
            banner.style.display = 'block'; // Показуємо банер

            // Через 10 секунд повертаємо все до норми
            setTimeout(() => {
                isDegraded = false;
                errorsCount = 0;
                btn.disabled = false;
                btn.innerText = "Відправити замовлення";
                banner.style.display = 'none';
            }, 10000); // 10 секунд
        }
    }
}