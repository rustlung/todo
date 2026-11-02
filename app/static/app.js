document.addEventListener("click", (event) => {
  const editButton = event.target.closest(".edit-button");
  const cancelButton = event.target.closest(".cancel-edit");

  if (editButton) {
    document.querySelectorAll(".edit-form:not([hidden])").forEach((form) => {
      form.hidden = true;
      form.closest(".task").querySelector(".task-title").hidden = false;
    });

    const task = editButton.closest(".task");
    task.querySelector(".task-title").hidden = true;
    task.querySelector(".edit-form").hidden = false;
    task.querySelector(".edit-form input[name='title']").focus();
  }

  if (cancelButton) {
    const task = cancelButton.closest(".task");
    task.querySelector(".edit-form").hidden = true;
    task.querySelector(".task-title").hidden = false;
  }
});

document.addEventListener("submit", (event) => {
  if (event.target.matches(".delete-form") && !window.confirm("Удалить эту задачу?")) {
    event.preventDefault();
  }
});
