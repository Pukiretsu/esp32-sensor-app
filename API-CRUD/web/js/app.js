// scripts.js
const API_ADDR = "http://127.0.0.1:8080"
$(document).ready(function () {
  // Mostrar la sección de Inicio por defecto
  $('#inicio-section').addClass('active');
  $('#inicio-link').addClass('active');

  // Función para formatear la fecha y hora
  function time_utc_to_local(horaUtcStr) {
    const [hora, minuto, segundoMs] = horaUtcStr.split(':');
    const [segundo] = segundoMs.split('.'); // ignoramos los milisegundos

    const ahora = new Date();
    const fechaUtc = new Date(Date.UTC(
      ahora.getFullYear(),
      ahora.getMonth(),
      ahora.getDate(),
      parseInt(hora),
      parseInt(minuto),
      parseInt(segundo)
    ));

    // Convertir a hora local en formato 12 horas sin segundos
    return fechaUtc.toLocaleTimeString('es-CO', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  }

  function formatearFecha(fechaIsoStr) {
    const fecha = new Date(fechaIsoStr + "T00:00:00Z"); // Le agregamos la hora para que no se confunda con local

    const opciones = {
      weekday: 'short',  // Día de la semana abreviado (lun, mar, etc.)
      day: '2-digit',
      month: 'short',    // Mes abreviado (ene, feb, etc.)
      year: 'numeric'
    };

    return new Intl.DateTimeFormat('es-CO', opciones).format(fecha);
  }

  // Función para generar un aviso de que no se han generado datos aún
  function generar_alerta_no_data(contenedorId) {
    let header = $('<h2> No hay datos para mostrar 😢</h2>');
    $('#' + contenedorId).html(header);
  }


  let intervalo;
  let ultimoId = 0;
  let lastLogId;
  let lastSensorId;

  function actualizarTablaLogs() {
    $.get(API_ADDR + '/logs', function (data) {
      const tbody = $('#logs-table table tbody');

      // Ordenar por ID por si vienen desordenados
      data.sort((a, b) => b.id - a.id);
      data.forEach(item => {
        if (item.id > lastLogId) {
          let fila = $('<tr class="new-row"></tr>');
          fila.append('<td>' + item.id + '</td>');
          fila.append('<td>' + formatearFecha(item.fecha), + '</td>');
          fila.append('<td>' + time_utc_to_local(item.hora) + '</td>');
          fila.append('<td>' + item.tag + '</td>');
          fila.append('<td>' + item.evento + '</td>');
          tbody.prepend(fila);

          // Actualizar el último ID visto
          if (item.id > lastLogId) {
            lastLogId = item.id;
          }

          // Remover clase de resaltado después de 3 segundos
          setTimeout(() => {
            fila.removeClass('new-row');
          }, 5000);
        }
      });
    });
  }

  function actualizarTablaSensores() {
    $.get(API_ADDR + '/sensor', function (data) {
      const tbody = $('#sensor-table table tbody');

      // Ordenar por ID por si vienen desordenados
      data.sort((a, b) => b.id - a.id);
      data.forEach(item => {
        if (item.id > lastSensorId) {
          let fila = $('<tr class="new-row"></tr>');
          fila.append('<td>' + item.id + '</td>');
          fila.append('<td>' + time_utc_to_local(item.hora) + '</td>');
          fila.append('<td>' + formatearFecha(item.fecha), + '</td>');
          fila.append('<td>' + item.tipo + '</td>');
          fila.append('<td>' + item.temperatura + '</td>');
          fila.append('<td>' + item.humedad + '</td>');
          tbody.prepend(fila);

          // Actualizar el último ID visto
          if (item.id > lastSensorId) {
            lastSensorId = item.id;
          }

          // Remover clase de resaltado después de 3 segundos
          setTimeout(() => {
            fila.removeClass('new-row');
          }, 3000);
        }
      });
    });
  }



  function activarActualizacionTabla(contenedorId) {
    vistaActiva = contenedorId;

    if (!intervalo) {
      if (contenedorId === 'logs-table') {
        actualizarTablaLogs(); // primer fetch
        intervalo = setInterval(actualizarTablaLogs, 1000);
      } else if (contenedorId === 'sensor-table') {
        actualizarTablaSensores(); // primer fetch
        intervalo = setInterval(actualizarTablaSensores, 5000);
      }
    }
  }

  function desactivarActualizacionTabla() {
    clearInterval(intervalo);
    intervalo = null;
    ultimoId = 0;
  }

  // Función para generar tablas
  function generarTabla(datos, contenedorId) {
    // organizar los datos en orden ascendente
    datos.sort((a, b) => b.id - a.id);
    // Crear la tabla
    let tabla = $('<table></table>');
    if (contenedorId === 'logs-table') {
      lastLogId = datos[0].id;
      let encabezado = $('<tr></tr>');
      encabezado.append('<th class="col-id">ID</th>');
      encabezado.append('<th class="col-hora">Hora</th>');
      encabezado.append('<th class="col-fecha">Fecha</th>');
      encabezado.append('<th class="col-tag">Tag</th>');
      encabezado.append('<th class="col-evento">Evento</th>');
      tabla.append(encabezado);
      tabla.append('<tbody>');

      // Llenar la tabla con los datos obtenidos de la API
      datos.forEach(function (item) {
        let fila = $('<tr></tr>');
        fila.append('<td>' + item.id + '</td>');
        fila.append('<td>' + time_utc_to_local(item.hora) + '</td>');
        fila.append('<td>' + formatearFecha(item.fecha), + '</td>');
        fila.append('<td>' + item.tag + '</td>');
        fila.append('<td>' + item.evento + '</td>');
        tabla.append(fila);
      });
    } else if (contenedorId === 'sensor-table') {
      lastSensorId = datos[0].id;
      let encabezado = $('<tr></tr>');
      encabezado.append('<th class="col-id">ID</th>');
      encabezado.append('<th class="col-hora">Hora</th>');
      encabezado.append('<th class="col-fecha">Fecha</th>');
      encabezado.append('<th class="col-sensor">Sensor N.</th>');
      encabezado.append('<th class="col-temperatura">Temperatura °C</th>');
      encabezado.append('<th class="col-humedad">Humedad (%)</th>');
      tabla.append(encabezado);
      tabla.append('<tbody>');

      // Llenar la tabla con los datos obtenidos de la API
      datos.forEach(function (item) {
        let fila = $('<tr></tr>');
        fila.append('<td>' + item.id + '</td>');
        fila.append('<td>' + time_utc_to_local(item.hora) + '</td>');
        fila.append('<td>' + formatearFecha(item.fecha), + '</td>');
        fila.append('<td>' + item.tipo + '</td>');
        fila.append('<td>' + item.temperatura + '</td>');
        fila.append('<td>' + item.humedad + '</td>');
        tabla.append(fila);
      });
    }
    tabla.append('</tbody>');
    // Colocar la tabla en el contenedor adecuado
    $('#' + contenedorId).html(tabla);
  }

  // Función para manejar el clic en los enlaces de la barra de navegación
  $('.nav-item').on('click', function (e) {
    e.preventDefault();  // Evitar el comportamiento predeterminado del enlace

    // Obtener el id de la sección correspondiente
    var sectionId = $(this).attr('id').replace('-link', '-section');

    // Ocultar todas las secciones y quitar la clase 'active' de los enlaces
    $('.section').removeClass('active');
    $('.nav-item').removeClass('active');

    // Mostrar la sección correspondiente y marcar el enlace como activo
    $('#' + sectionId).addClass('active');
    $(this).addClass('active');

    if ($(this).attr('id') !== 'logs-link' || $(this).attr('id') !== 'sensor-link') {
      desactivarActualizacionTabla();
    }

    // Ejecutar funciones específicas según la pestaña seleccionada
    if ($(this).attr('id') === 'logs-link') {
      // Llamar a la API para los Logs y generar la tabla
      $.get(API_ADDR + '/logs', function (datos) {
        if (datos.length !== 0) {
          generarTabla(datos, 'logs-table');
          activarActualizacionTabla('logs-table')
        } else {
          sin_datos_element('logs-table');
        }

      });
    } else if ($(this).attr('id') === 'sensor-link') {
      // Llamar a la API para los Datos Sensor y generar la tabla
      $.get(API_ADDR + '/sensor', function (datos) {
        if (datos.length !== 0) {
          generarTabla(datos, 'sensor-table');
          activarActualizacionTabla('sensor-table')
        } else {
          generar_alerta_no_data('sensor-table');
        }
      });
    }
  });
});
