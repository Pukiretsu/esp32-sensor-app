// static/js/app.js

// La API ahora se sirve desde el mismo dominio, y todas las rutas API inician con /api/
const API_ADDR = "/api";

$(document).ready(function () {
    // Función para formatear la fecha a 'lun, 01 ene, 2023'
    function formatIsoDateForDisplay(isoString) {
        const date = new Date(isoString);
        const options = {
            weekday: 'short',
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        };
        return new Intl.DateTimeFormat('es-CO', options).format(date);
    }

    // Función para formatear la hora a 'HH:MM:SS AM/PM'
    function formatIsoTimeForDisplay(isoString) {
        const date = new Date(isoString);
        const options = {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit', // Incluir segundos para mayor precisión
            hour12: true
        };
        return new Intl.DateTimeFormat('es-CO', options).format(date);
    }

    // Función para generar un aviso de que no se han generado datos aún
    function generar_alerta_no_data(contenedorId) {
        let header = $('<h2> No hay datos para mostrar 😢</h2>');
        $('#' + contenedorId).html(header);
    }

    let intervaloActualizacion; // Variable para almacenar el intervalo de actualización
    let lastSensorTimestamp = ''; // Usaremos el timestamp como último "ID" para el sensor
    let currentControllerUuid = null; // UUID del controlador actualmente seleccionado
    let currentEnsayoUuid = null; // UUID del ensayo actualmente seleccionado

    // --- Lógica específica para la página de Inicio ---
    if (window.location.pathname === '/') {
        fetchLatestSensorData(); // Cargar la última lectura al iniciar la página
    }

    // Función para actualizar las "Lecturas rápidas" en la sección de inicio
    function fetchLatestSensorData() {
        $.get(API_ADDR + '/sensor/latest', function (data) {
            if (data) {
                $('#esp32-status').text('Activo'); // Asumimos activo si hay datos
                $('#current-temperature').text(data.lectura_temperatura.toFixed(2));
                $('#current-humidity').text(data.lectura_humedad.toFixed(2));
            } else {
                $('#esp32-status').text('Inactivo');
                $('#current-temperature').text('-');
                $('#current-humidity').text('-');
            }
        }).fail(function() {
            console.error("Error al cargar datos de la última lectura del sensor.");
            $('#esp32-status').text('Error al cargar');
            $('#current-temperature').text('-');
            $('#current-humidity').text('-');
        });
    }

    // --- Lógica específica para la página de Datos de Sensores ---
    if (window.location.pathname === '/datos') {
        loadControllers(); // Cargar la lista de controladores al entrar a la página de datos

        // Event listener para el botón de registrar controlador
        $('#register-controller-btn').on('click', function () {
            const controllerName = $('#new-controller-name').val();
            if (controllerName) {
                registerController(controllerName);
            } else {
                alert('Por favor, ingresa un nombre para el controlador.');
            }
        });

        // Event listener para el botón de registrar ensayo (solo visible cuando se selecciona un controlador)
        $('#register-ensayo-btn').on('click', function () {
            const ensayoName = $('#new-ensayo-name').val();
            if (ensayoName && currentControllerUuid) {
                registerEnsayo(ensayoName, currentControllerUuid);
            } else if (!ensayoName) {
                alert('Por favor, ingresa un nombre para el ensayo.');
            } else {
                alert('Por favor, selecciona un controlador primero.');
            }
        });

        // Event listener para el botón de refrescar datos del sensor (del controlador seleccionado)
        $('#refresh-sensor-btn').on('click', function () {
            if (currentControllerUuid) {
                actualizarTablaSensores(currentControllerUuid, currentEnsayoUuid);
                console.log("Actualizando sensores para el controlador: " + currentControllerUuid + (currentEnsayoUuid ? " y ensayo: " + currentEnsayoUuid : " (todos los ensayos)"));
            } else {
                console.warn("No hay controlador seleccionado para refrescar los datos.");
            }
        });

        // Event listener para el botón de exportar datos del sensor (del controlador seleccionado)
        $('#export-sensor-btn').on('click', function () {
            if (currentControllerUuid) {
                let url = API_ADDR + '/sensor/?uuid_controlador=' + currentControllerUuid;
                if (currentEnsayoUuid) {
                    url += '&uuid_ensayo=' + currentEnsayoUuid;
                }
                $.get(url, function (data) {
                    if (data.length > 0) {
                        const csvData = convertToCSV(data, false); // isLogs = false para datos de sensor
                        downloadCSV(csvData, `sensores_${currentControllerUuid}_${currentEnsayoUuid || 'todos'}_${new Date().toISOString().slice(0, 10)}.csv`);
                    } else {
                        alert('No hay datos de sensores para exportar para este controlador/ensayo.');
                    }
                }).fail(function () {
                    alert('Error al obtener datos de sensores para exportar.');
                });
            } else {
                alert('Por favor, selecciona un controlador para exportar sus datos.');
            }
        });

        // Event listener para el filtro de ensayos
        $('#ensayo-filter').on('change', function() {
            currentEnsayoUuid = $(this).val();
            if (currentControllerUuid) {
                actualizarTablaSensores(currentControllerUuid, currentEnsayoUuid);
            }
        });

        // Event listener para el botón "Mostrar Todas las Lecturas"
        $('#show-all-data-btn').on('click', function() {
            $('#ensayo-filter').val(''); // Resetea el filtro de ensayo
            currentEnsayoUuid = null;
            if (currentControllerUuid) {
                actualizarTablaSensores(currentControllerUuid, null); // Muestra todos los datos del controlador
            }
        });
    }

    // Función para cargar y mostrar la lista de controladores
    function loadControllers() {
        $.get(API_ADDR + '/controladores/', function (data) {
            const controllersListDiv = $('#controladores-list');
            controllersListDiv.empty(); // Limpiar la lista existente

            if (data.length > 0) {
                data.forEach(controller => {
                    const controllerCard = `
                        <div class="sensor-card controller-card" data-uuid="${controller.uuid_controlador}">
                            <span class="material-symbols-outlined sensor-icon">developer_board</span>
                            <h3>${controller.nombre_controlador}</h3>
                            <p>UUID: ${controller.uuid_controlador}</p>
                            <p>Registrado: ${formatIsoDateForDisplay(controller.timestamp_registro)}</p>
                            <button class="btn btn-primary view-data-btn" data-uuid="${controller.uuid_controlador}" data-name="${controller.nombre_controlador}">
                                Ver Datos
                            </button>
                            <button class="btn btn-danger delete-controller-btn" data-uuid="${controller.uuid_controlador}">
                                <span class="material-symbols-outlined">delete</span>
                                Eliminar
                            </button>
                        </div>
                    `;
                    controllersListDiv.append(controllerCard);
                });

                // Añadir event listeners a los botones "Ver Datos"
                $('.view-data-btn').on('click', function () {
                    const uuid = $(this).data('uuid');
                    const name = $(this).data('name');
                    selectController(uuid, name);
                });

                // Añadir event listeners a los botones "Eliminar Controlador"
                $('.delete-controller-btn').on('click', function (e) {
                    e.stopPropagation(); // Evitar que el clic en eliminar active "Ver Datos"
                    const uuid = $(this).data('uuid');
                    if (confirm(`¿Estás seguro de que quieres eliminar el controlador con UUID: ${uuid}? Esto eliminará también todos los ensayos y lecturas asociadas.`)) {
                        deleteController(uuid);
                    }
                });

            } else {
                controllersListDiv.append('<p>No hay controladores registrados aún.</p>');
            }
        }).fail(function () {
            console.error("Error al cargar la lista de controladores.");
            $('#controladores-list').html('<p>Error al cargar controladores. Intenta refrescar la página.</p>');
        });
    }

    // Función para registrar un nuevo controlador
    function registerController(name) {
        $.ajax({
            url: API_ADDR + '/controladores/',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ nombre_controlador: name }),
            success: function (response) {
                $('#registered-uuid-display').text(`Controlador "${response.nombre_controlador}" registrado con UUID: ${response.uuid_controlador}`);
                $('#new-controller-name').val(''); // Limpiar el input
                loadControllers(); // Recargar la lista de controladores
            },
            error: function (jqXHR, textStatus, errorThrown) {
                console.error("Error al registrar controlador:", jqXHR.responseJSON || errorThrown);
                alert('Error al registrar controlador: ' + (jqXHR.responseJSON ? jqXHR.responseJSON.detail : errorThrown));
            }
        });
    }

    // Función para eliminar un controlador
    function deleteController(uuid) {
        $.ajax({
            url: API_ADDR + '/controladores/' + uuid,
            type: 'DELETE',
            success: function () {
                alert('Controlador eliminado exitosamente.');
                loadControllers(); // Recargar la lista de controladores
                // Si el controlador eliminado era el seleccionado, ocultar la vista de datos
                if (currentControllerUuid === uuid) {
                    $('#controller-details-section').hide(); // Ocultar toda la sección de detalles
                    currentControllerUuid = null;
                    currentEnsayoUuid = null; // Resetear ensayo seleccionado
                    if (intervaloActualizacion) {
                        clearInterval(intervaloActualizacion);
                        intervaloActualizacion = null;
                    }
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                console.error("Error al eliminar controlador:", jqXHR.responseJSON || errorThrown);
                alert('Error al eliminar controlador: ' + (jqXHR.responseJSON ? jqXHR.responseJSON.detail : errorThrown));
            }
        });
    }

    // Función para cargar y mostrar la lista de ensayos para un controlador específico
    function loadEnsayos(controllerUuid) {
        $.get(API_ADDR + '/ensayos/?uuid_controlador=' + controllerUuid, function (data) {
            const ensayosListDiv = $('#ensayos-list');
            ensayosListDiv.empty(); // Limpiar la lista existente

            const ensayoFilterSelect = $('#ensayo-filter');
            ensayoFilterSelect.empty(); // Limpiar opciones existentes
            ensayoFilterSelect.append('<option value="">Todos los Ensayos</option>'); // Opción por defecto

            if (data.length > 0) {
                data.forEach(ensayo => {
                    const ensayoCard = `
                        <div class="sensor-card ensayo-card" data-uuid="${ensayo.uuid_ensayo}">
                            <span class="material-symbols-outlined sensor-icon">science</span>
                            <h3>${ensayo.nombre_ensayo}</h3>
                            <p>UUID: ${ensayo.uuid_ensayo}</p>
                            <p>Registrado: ${formatIsoDateForDisplay(ensayo.timestamp_registro)}</p>
                            <button class="btn btn-danger delete-ensayo-btn" data-uuid="${ensayo.uuid_ensayo}">
                                <span class="material-symbols-outlined">delete</span>
                                Eliminar
                            </button>
                        </div>
                    `;
                    ensayosListDiv.append(ensayoCard);
                    ensayoFilterSelect.append(`<option value="${ensayo.uuid_ensayo}">${ensayo.nombre_ensayo}</option>`);
                });

                // Añadir event listeners a los botones "Eliminar Ensayo"
                $('.delete-ensayo-btn').on('click', function () {
                    const uuid = $(this).data('uuid');
                    if (confirm(`¿Estás seguro de que quieres eliminar el ensayo con UUID: ${uuid}? Esto eliminará también todas las lecturas asociadas.`)) {
                        deleteEnsayo(uuid);
                    }
                });

            } else {
                ensayosListDiv.append('<p>No hay ensayos registrados para este controlador.</p>');
            }
        }).fail(function () {
            console.error("Error al cargar la lista de ensayos.");
            $('#ensayos-list').html('<p>Error al cargar ensayos. Intenta refrescar la página.</p>');
        });
    }

    // Función para registrar un nuevo ensayo
    function registerEnsayo(name, controllerUuid) {
        $.ajax({
            url: API_ADDR + '/ensayos/',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ nombre_ensayo: name, uuid_controlador: controllerUuid }),
            success: function (response) {
                $('#registered-ensayo-uuid-display').text(`Ensayo "${response.nombre_ensayo}" registrado con UUID: ${response.uuid_ensayo}`);
                $('#new-ensayo-name').val(''); // Limpiar el input
                loadEnsayos(controllerUuid); // Recargar la lista de ensayos para el controlador actual
            },
            error: function (jqXHR, textStatus, errorThrown) {
                console.error("Error al registrar ensayo:", jqXHR.responseJSON || errorThrown);
                alert('Error al registrar ensayo: ' + (jqXHR.responseJSON ? jqXHR.responseJSON.detail : errorThrown));
            }
        });
    }

    // Función para eliminar un ensayo
    function deleteEnsayo(uuid) {
        $.ajax({
            url: API_ADDR + '/ensayos/' + uuid,
            type: 'DELETE',
            success: function () {
                alert('Ensayo eliminado exitosamente.');
                loadEnsayos(currentControllerUuid); // Recargar la lista de ensayos para el controlador actual
                actualizarTablaSensores(currentControllerUuid, currentEnsayoUuid); // Refrescar lecturas por si se eliminó un ensayo con lecturas
            },
            error: function (jqXHR, textStatus, errorThrown) {
                console.error("Error al eliminar ensayo:", jqXHR.responseJSON || errorThrown);
                alert('Error al eliminar ensayo: ' + (jqXHR.responseJSON ? jqXHR.responseJSON.detail : errorThrown));
            }
        });
    }


    // Función para seleccionar un controlador y mostrar sus datos y ensayos
    function selectController(uuid, name) {
        currentControllerUuid = uuid;
        currentEnsayoUuid = null; // Resetear el ensayo seleccionado al cambiar de controlador

        $('#selected-controller-name').text(name);
        $('#selected-controller-uuid-display').text(uuid); // Mostrar UUID del controlador
        $('#ensayos-controller-name').text(name); // Nombre del controlador en sección de ensayos
        $('#lecturas-controller-name').text(name); // Nombre del controlador en sección de lecturas

        $('#controller-details-section').show(); // Mostrar toda la sección de detalles del controlador
        
        $('#ensayo-filter').val(''); // Resetear el dropdown de filtro

        loadEnsayos(uuid); // Cargar los ensayos para el controlador seleccionado
        actualizarTablaSensores(uuid, null); // Cargar todos los datos del controlador seleccionado inicialmente

        // Desactivar el intervalo de actualización si estaba activo para otro controlador
        if (intervaloActualizacion) {
            clearInterval(intervaloActualizacion);
        }
        // Iniciar la actualización automática para este controlador (todos los ensayos)
        intervaloActualizacion = setInterval(() => actualizarTablaSensores(uuid, null), 10000);
    }

    // Función para actualizar la tabla de sensores de un controlador específico, opcionalmente filtrado por ensayo
    function actualizarTablaSensores(controllerUuid, ensayoUuid = null) {
        let url = API_ADDR + '/sensor/?uuid_controlador=' + controllerUuid;
        if (ensayoUuid) {
            url += '&uuid_ensayo=' + ensayoUuid;
        }

        $.get(url, function (data) {
            const sensorTableDiv = $('#sensor-table');
            sensorTableDiv.empty(); // Limpiar la tabla existente

            if (data.length > 0) {
                // Ordenar por timestamp de forma descendente (más recientes primero)
                data.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

                let tabla = $('<table></table>');
                let thead = $('<thead></thead>');
                let tbody = $('<tbody></tbody>');

                let encabezado = $('<tr></tr>');
                encabezado.append('<th class="col-id">Timestamp</th>');
                encabezado.append('<th class="col-fecha">Fecha</th>');
                encabezado.append('<th class="col-hora">Hora</th>');
                encabezado.append('<th class="col-sensor">Sensor N.</th>');
                encabezado.append('<th class="col-ensayo">Ensayo</th>'); // Nueva columna para Ensayo
                encabezado.append('<th class="col-temperatura">Temperatura °C</th>');
                encabezado.append('<th class="col-humedad">Humedad (%)</th>');
                thead.append(encabezado);
                tabla.append(thead);

                data.forEach(item => {
                    let fila = $('<tr></tr>');
                    fila.append('<td>' + item.timestamp + '</td>');
                    fila.append('<td>' + formatIsoDateForDisplay(item.timestamp) + '</td>');
                    fila.append('<td>' + formatIsoTimeForDisplay(item.timestamp) + '</td>');
                    fila.append('<td>' + item.id_sensor + '</td>');
                    fila.append('<td>' + item.nombre_ensayo + '</td>'); // Mostrar nombre del ensayo
                    fila.append('<td>' + item.lectura_temperatura.toFixed(2) + '</td>');
                    fila.append('<td>' + item.lectura_humedad.toFixed(2) + '</td>');
                    tbody.append(fila);
                });
                tabla.append(tbody);
                sensorTableDiv.html(tabla);
            } else {
                generar_alerta_no_data('sensor-table');
            }
        }).fail(function () {
            console.error("Error al cargar datos de sensores para el controlador " + controllerUuid + (ensayoUuid ? " y ensayo " + ensayoUuid : ""));
            generar_alerta_no_data('sensor-table');
        });
    }

    // Función para actualizar la tabla de logs (sin cambios en JS, pero la API no la soporta)
    function actualizarTablaLogs() {
        console.warn("La API actual no tiene un endpoint para 'logs' con la estructura esperada.");
        generar_alerta_no_data('logs-table');
    }

    // Función para convertir datos a CSV
    function convertToCSV(data, isLogs = true) {
        const headers = isLogs
            ? ['ID', 'Fecha', 'Hora', 'Tag', 'Evento'] // No se usará para la API actual
            : ['Timestamp', 'Fecha', 'Hora', 'Sensor N.', 'Ensayo', 'Temperatura', 'Humedad']; // Headers actualizados

        const rows = data.map(item => {
            if (isLogs) {
                // Este bloque de logs no se usará con la API actual
                return [
                    item.id,
                    item.fecha,
                    item.hora,
                    `"${item.tag.replace(/"/g, '""')}"`,
                    `"${item.evento.replace(/"/g, '""')}"`
                ].join(',');
            } else {
                return [
                    item.timestamp,
                    formatIsoDateForDisplay(item.timestamp),
                    formatIsoTimeForDisplay(item.timestamp),
                    item.id_sensor,
                    `"${item.nombre_ensayo.replace(/"/g, '""')}"`, // Incluir nombre del ensayo
                    item.lectura_temperatura,
                    item.lectura_humedad
                ].join(',');
            }
        });

        return [headers.join(','), ...rows].join('\n');
    }

    // Función para descargar el archivo CSV
    function downloadCSV(csvData, filename) {
        const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);

        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
});
